import asyncio
import logging
import shutil
import subprocess
import time

import aiohttp

logger = logging.getLogger(__name__)


class ServiceHealth:
    """Represents the health status of a service.

    Attributes:
        name: The name of the service.
        url: The URL of the service to check.
        healthy: Whether the service is healthy.
        status_code: The HTTP status code returned by the service.
        response_time: The response time in milliseconds.
        error: Any error message encountered during the check.
    """

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.healthy: bool = False
        self.status_code: int | None = None
        self.response_time: float | None = None
        self.error: str | None = None


async def check_service_health(
    service: ServiceHealth, session: aiohttp.ClientSession
) -> None:
    """Perform an HTTP health check on a single service.

    Makes an HTTP GET request to the service URL and updates the
    ServiceHealth object with the results (status code, response time, errors).

    Args:
        service: The ServiceHealth object to check and update in place.
        session: The aiohttp ClientSession to use for making requests.
    """
    try:
        start_time = time.perf_counter()
        async with session.get(
            service.url, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            service.response_time = (time.perf_counter() - start_time) * 1000
            service.status_code = response.status
            service.healthy = response.status < 500
            if response.status >= 400:
                service.error = f"HTTP {response.status}"
    except TimeoutError:
        service.error = "Timeout"
        service.healthy = False
    except Exception as e:
        service.error = str(e)
        service.healthy = False


async def check_all_services(services: list[ServiceHealth]) -> None:
    """Perform concurrent health checks on all provided services.

    Uses asyncio.gather to check multiple services in parallel,
    updating each ServiceHealth object in place with the results.

    Args:
        services: A list of ServiceHealth objects to check. Each object
            will be mutated to contain the health check results.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [check_service_health(service, session) for service in services]
        await asyncio.gather(*tasks)


def check_docker_containers() -> dict[str, bool]:
    """Query Docker to get the health status of all running containers.

    Executes `docker ps` and parses the output to determine which containers
    are healthy based on their status string.

    Returns:
        A dictionary mapping container names to their health status,
        where True indicates the container is healthy.
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}

    container_status = {}
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            name, status = parts
            container_status[name.replace("/", "")] = "healthy" in status.lower()

    return container_status


def _format_size(size: int) -> str:
    """Format a byte size into a human-readable string."""
    for unit in ["B", "K", "M", "G", "T", "P"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}E"


def check_disk_space() -> dict[str, str]:
    """Query the root filesystem for disk space usage.

    Uses shutil.disk_usage to get disk usage metrics.

    Returns:
        A dictionary with keys 'total', 'used', 'available', and 'usage_percent'.
    """
    try:
        total, used, free = shutil.disk_usage("/")
        
        # Calculate percentage
        percent = (used / total) * 100 if total > 0 else 0
        
        return {
            "total": _format_size(total),
            "used": _format_size(used),
            "available": _format_size(free),
            "usage_percent": f"{percent:.0f}%",
        }
    except Exception:
        return {}


def check_ssl_certificates(domain: str) -> dict[str, bool]:
    """Verify SSL certificate validity for core services.

    Attempts to establish SSL connections to traefik, grafana, and prometheus
    subdomains to validate their certificates are properly configured.

    Args:
        domain: The base domain to check certificates for (e.g., "example.com").

    Returns:
        A dictionary mapping service names to their SSL validity status,
        where True indicates a valid certificate.
    """
    try:
        import socket
        import ssl

        services_to_check = {
            "traefik": f"traefik.{domain}",
            "grafana": f"grafana.{domain}",
            "prometheus": f"prometheus.{domain}",
        }

        ssl_status = {}

        for service, hostname in services_to_check.items():
            try:
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        ssock.getpeercert()
                        ssl_status[service] = True
            except Exception as e:
                ssl_status[service] = False
                logger.warning(f"SSL check failed for {service}: {e}")

        return ssl_status
    except Exception:
        return {}
