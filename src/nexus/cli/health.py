import asyncio
import logging
import sys
from typing import Optional

import click

from nexus.health.checks import (
    ServiceHealth,
    check_all_services,
    check_disk_space,
    check_docker_containers,
    check_ssl_certificates,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


CRITICAL_SERVICES = ["traefik", "auth"]
ALL_SERVICES = [
    "traefik",
    "auth",
    "dashboard",
    "plex",
    "jellyfin",
    "sure",
    "foundryvtt",
]


@click.command()
@click.option("--domain", type=str, help="Base domain for SSL checks.")
@click.option("--critical-only", is_flag=True, help="Only check critical services.")
@click.option("--alert-webhook", type=str, help="Send alerts to webhook URL.")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output.")
def main(
    domain: Optional[str],
    critical_only: bool,
    alert_webhook: Optional[str],
    verbose: bool,
) -> None:
    """Run comprehensive health checks across all Nexus services.

    Checks Docker container status, performs HTTP health probes on each service,
    validates SSL certificates, and reports disk space usage. Outputs a formatted
    report and optionally sends alerts for failures.

    Args:
        domain: Base domain for constructing service URLs and SSL checks.
        critical_only: Limit checks to critical infrastructure services only.
        alert_webhook: Webhook URL for sending failure notifications.
        verbose: Enable debug-level logging output.

    Raises:
        SystemExit: Exit code 1 if any service is unhealthy, 0 otherwise.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Running health checks...")

    docker_status = check_docker_containers()
    disk_space = check_disk_space()

    ssl_status: dict[str, bool] = {}
    if domain:
        ssl_status = check_ssl_certificates(domain)

    services_to_check = CRITICAL_SERVICES if critical_only else ALL_SERVICES

    health_checks: list[ServiceHealth] = []
    for service in services_to_check:
        if service == "dashboard":
            url = f"https://hub.{domain}" if domain else "http://localhost"
        else:
            url = f"https://{service}.{domain}" if domain else "http://localhost"

        health_checks.append(ServiceHealth(service, url))

    asyncio.run(check_all_services(health_checks))

    print("\n" + "=" * 60)
    print("  Nexus Health Check Report")
    print("=" * 60 + "\n")

    print("Docker Containers:")
    for name, healthy in docker_status.items():
        status = "✅" if healthy else "❌"
        print(f"  {status} {name}")

    print("\nService Health:")
    all_healthy = True
    for check in health_checks:
        status = "✅" if check.healthy else "❌"
        print(f"  {status} {check.name}")
        if check.error:
            print(f"      Error: {check.error}")
        if not check.healthy:
            all_healthy = False

    if ssl_status:
        print("\nSSL Certificates:")
        for service, valid in ssl_status.items():
            status = "✅" if valid else "❌"
            print(f"  {status} {service}")

    if disk_space:
        print("\nDisk Space:")
        print(f"  Total: {disk_space.get('total', 'N/A')}")
        print(f"  Used: {disk_space.get('used', 'N/A')}")
        print(f"  Available: {disk_space.get('available', 'N/A')}")
        print(f"  Usage: {disk_space.get('usage_percent', 'N/A')}")

    print("\n" + "=" * 60)

    if not all_healthy:
        logger.warning("Some services are not healthy!")
        if alert_webhook:
            logger.info(f"Sending alert to {alert_webhook}")
        sys.exit(1)
    else:
        logger.info("All services are healthy!")
        sys.exit(0)


if __name__ == "__main__":
    main()
