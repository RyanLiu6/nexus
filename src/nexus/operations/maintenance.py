import logging
import subprocess

logger = logging.getLogger(__name__)


def _run_command(cmd: list[str], description: str) -> subprocess.CompletedProcess[str]:
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"✓ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed: {e.stderr}")
        raise


def check_container_status() -> bool:
    """Query Docker to check if all containers are running healthily.

    Runs `docker compose ps` and scans output for any exited containers
    to determine overall health status.

    Returns:
        True if all containers are running, False if any have exited.
    """
    result = _run_command(["docker", "compose", "ps"], "Check container status")

    unhealthy_services = [
        line for line in result.stdout.split("\n") if "Exited" in line
    ]

    if unhealthy_services:
        logger.warning(f"Unhealthy containers: {unhealthy_services}")
        return False
    return True


def check_disk_space() -> dict[str, str | int]:
    """Check root filesystem disk usage and warn if thresholds exceeded.

    Runs `df -h /` and logs warnings at 80% usage and errors at 90%.

    Returns:
        Dictionary with 'total', 'used', 'available' (strings) and
        'usage_percent' (int). Empty dict if parsing fails.
    """
    result = _run_command(["df", "-h", "/"], "Check disk space")

    lines = result.stdout.split("\n")
    if len(lines) > 1:
        parts = lines[1].split()
        usage_percent = int(parts[4].rstrip("%"))

        warning_threshold = 80
        critical_threshold = 90

        if usage_percent >= critical_threshold:
            logger.error(f"🚨 Critical disk usage: {usage_percent}%")
        elif usage_percent >= warning_threshold:
            logger.warning(f"⚠️  High disk usage: {usage_percent}%")

        return {
            "total": parts[1],
            "used": parts[2],
            "available": parts[3],
            "usage_percent": usage_percent,
        }

    return {}


def verify_backups() -> bool:
    """Check if backup snapshots exist in restic repositories.

    Uses `docker exec backrest restic snapshots` to verify backup snapshots exist.

    Returns:
        True if at least one backup snapshot is found, False otherwise.
    """
    try:
        result = _run_command(
            ["docker", "exec", "backrest", "restic", "snapshots"],
            "Check backup snapshots",
        )
        if result.stdout.strip():
            logger.info("✓ Backup snapshots found")
            return True
        logger.warning("No backup snapshots found")
        return False
    except subprocess.CalledProcessError:
        logger.error("Failed to check backup snapshots")
        return False


def check_service_logs() -> None:
    """Scan service logs from the last hour for error messages.

    Checks traefik, tailscale-access, and jellyfin container logs
    and logs a warning if errors are found.
    """
    services = ["traefik", "tailscale-access", "jellyfin"]

    for service in services:
        result = subprocess.run(
            ["docker", "logs", "--since", "1h", service],
            capture_output=True,
            text=True,
        )

        errors = [line for line in result.stdout.split("\n") if "error" in line.lower()]
        if errors:
            logger.warning(f"{service}: Found {len(errors)} errors in last hour")


def cleanup_old_images() -> None:
    """Remove all unused Docker images to reclaim disk space.

    Runs `docker image prune -a -f` to remove images not associated
    with any container.
    """
    logger.info("Cleaning up unused Docker images...")

    result = _run_command(
        ["docker", "image", "prune", "-a", "-f"], "Clean up Docker images"
    )

    freed_space = result.stdout.strip()
    logger.info(f"✓ Freed space: {freed_space}")


def cleanup_old_volumes() -> None:
    """Remove all unused Docker volumes to reclaim disk space.

    Runs `docker volume prune -f` to remove volumes not used by
    any container.
    """
    logger.info("Cleaning up unused Docker volumes...")

    result = _run_command(
        ["docker", "volume", "prune", "-f"], "Clean up Docker volumes"
    )

    freed_space = result.stdout.strip()
    logger.info(f"✓ Cleaned volumes: {freed_space}")


def daily_tasks() -> None:
    """Execute daily maintenance checks.

    Runs container status check, disk space check, and log scanning.
    """
    logger.info("📅 Running daily tasks...")

    check_container_status()
    check_disk_space()
    check_service_logs()

    logger.info("✓ Daily tasks complete")


def weekly_tasks() -> None:
    """Execute weekly maintenance operations.

    Verifies backups exist and cleans up unused Docker resources.
    """
    logger.info("📅 Running weekly tasks...")

    verify_backups()
    cleanup_old_images()
    cleanup_old_volumes()

    logger.info("✓ Weekly tasks complete")


def monthly_tasks() -> None:
    """Execute monthly maintenance reminders.

    Logs a reminder to consider rotating secrets.
    """
    logger.info("📅 Running monthly tasks...")

    logger.info("⚠️  Monthly reminder: Consider rotating secrets")
    logger.info("   Run: ansible-vault rekey ansible/vars/vault.yml")

    logger.info("✓ Monthly tasks complete")
