import asyncio
import logging
import subprocess
from typing import Optional

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
        self.status_code: Optional[int] = None
        self.response_time: Optional[float] = None
        self.error: Optional[str] = None


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
        start_time = asyncio.get_event_loop().time()
        async with session.get(
            service.url, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            service.response_time = (
                asyncio.get_event_loop().time() - start_time
            ) * 1000
            service.status_code = response.status
            service.healthy = response.status < 500
            if response.status >= 400:
                service.error = f"HTTP {response.status}"
    except asyncio.TimeoutError:
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
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
        capture_output=True,
        text=True,
    )

    container_status = {}
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            name, status = parts
            container_status[name.replace("/", "")] = "healthy" in status.lower()

    return container_status


def check_disk_space() -> dict[str, str]:
    """Query the root filesystem for disk space usage.

    Executes `df -h /` and parses the output to extract disk usage metrics.

    Returns:
        A dictionary with keys 'total', 'used', 'available', and 'usage_percent',
        or an empty dict if parsing fails.
    """
    result = subprocess.run(
        ["df", "-h", "/"],
        capture_output=True,
        text=True,
    )

    lines = result.stdout.splitlines()
    if len(lines) > 1:
        parts = lines[1].split()
        return {
            "total": parts[1],
            "used": parts[2],
            "available": parts[3],
            "usage_percent": parts[4],
        }
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
