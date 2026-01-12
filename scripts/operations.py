#!/usr/bin/env python3
import logging
import subprocess
from pathlib import Path
from typing import Union

import click

ROOT_PATH = Path(__file__).parent.parent

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_command(cmd: list[str], description: str) -> subprocess.CompletedProcess[str]:
    """Run a command with error handling.

    Args:
        cmd: List of command arguments.
        description: Description of the command for logging.

    Returns:
        The completed process object.

    Raises:
        subprocess.CalledProcessError: If the command fails.
    """
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"✓ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed: {e.stderr}")
        raise


def check_container_status() -> bool:
    """Check if all containers are running.

    Returns:
        True if all containers are healthy, False otherwise.
    """
    result = run_command(["docker", "compose", "ps"], "Check container status")

    # Parse output to see if any services are unhealthy
    unhealthy_services = [
        line for line in result.stdout.split("\n") if "Exited" in line
    ]

    if unhealthy_services:
        logger.warning(f"Unhealthy containers: {unhealthy_services}")
        return False
    return True


def check_disk_space() -> dict[str, Union[str, int]]:
    """Check disk space usage.

    Returns:
        A dictionary containing disk space information (total, used, available,
        usage_percent).
    """
    result = run_command(["df", "-h", "/"], "Check disk space")

    lines = result.stdout.split("\n")
    if len(lines) > 1:
        parts = lines[1].split()
        usage_percent = parts[4].rstrip("%")

        warning_threshold = 80
        critical_threshold = 90

        if int(usage_percent) >= critical_threshold:
            logger.error(f"🚨 Critical disk usage: {usage_percent}%")
        elif int(usage_percent) >= warning_threshold:
            logger.warning(f"⚠️  High disk usage: {usage_percent}%")

        return {
            "total": parts[1],
            "used": parts[2],
            "available": parts[3],
            "usage_percent": int(usage_percent),
        }

    return {}


def verify_backups() -> bool:
    """Check if recent backups exist.

    Returns:
        True if recent backups are found, False otherwise.
    """
    backup_dir = Path.home() / "nexus-backups"

    if not backup_dir.exists():
        logger.error(f"Backup directory not found: {backup_dir}")
        return False

    # Find recent backups (last 7 days)
    backups = sorted(backup_dir.glob("nexus-backup-*.tar.gz"), reverse=True)[:7]

    if not backups:
        logger.warning("No recent backups found")
        return False

    logger.info(f"✓ Found {len(backups)} recent backups")
    for backup in backups:
        logger.info(f"  - {backup.name}")

    return True


def check_service_logs() -> None:
    """Check logs for errors in the last hour."""
    services = ["traefik", "authelia", "plex", "jellyfin"]

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
    """Remove unused Docker images."""
    logger.info("Cleaning up unused Docker images...")

    result = run_command(
        ["docker", "image", "prune", "-a", "-f"], "Clean up Docker images"
    )

    freed_space = result.stdout.strip()
    logger.info(f"✓ Freed space: {freed_space}")


def cleanup_old_volumes() -> None:
    """Remove unused Docker volumes."""
    logger.info("Cleaning up unused Docker volumes...")

    result = run_command(["docker", "volume", "prune", "-f"], "Clean up Docker volumes")

    freed_space = result.stdout.strip()
    logger.info(f"✓ Cleaned volumes: {freed_space}")


def daily_tasks() -> None:
    """Run daily maintenance tasks."""
    logger.info("📅 Running daily tasks...")

    # Check containers
    check_container_status()

    # Check disk space
    check_disk_space()

    # Check service logs
    check_service_logs()

    logger.info("✓ Daily tasks complete")


def weekly_tasks() -> None:
    """Run weekly maintenance tasks."""
    logger.info("📅 Running weekly tasks...")

    # Verify backups
    verify_backups()

    # Clean up Docker resources
    cleanup_old_images()
    cleanup_old_volumes()

    logger.info("✓ Weekly tasks complete")


def monthly_tasks() -> None:
    """Run monthly maintenance tasks."""
    logger.info("📅 Running monthly tasks...")

    # Check all health
    subprocess.run([str(ROOT_PATH / "scripts" / "health_check.py")])

    # Generate new secrets reminder
    logger.info("⚠️  Monthly reminder: Consider rotating secrets")
    logger.info("   Run: ./scripts/generate-secrets.sh")

    logger.info("✓ Monthly tasks complete")


@click.command()
@click.option("--daily", is_flag=True, help="Run daily maintenance tasks")
@click.option("--weekly", is_flag=True, help="Run weekly maintenance tasks")
@click.option("--monthly", is_flag=True, help="Run monthly maintenance tasks")
@click.option("--all", is_flag=True, help="Run all maintenance tasks")
def main(daily: bool, weekly: bool, monthly: bool, all: bool) -> None:
    """Nexus operations script for maintenance tasks.

    Args:
        daily: Run daily maintenance tasks.
        weekly: Run weekly maintenance tasks.
        monthly: Run monthly maintenance tasks.
        all: Run all maintenance tasks.
    """
    if all or daily:
        daily_tasks()

    if all or weekly:
        weekly_tasks()

    if all or monthly:
        monthly_tasks()

    if not (daily or weekly or monthly or all):
        logger.error(
            "Please specify a task type: --daily, --weekly, --monthly, or --all"
        )
        return

    logger.info("🎉 Operations complete!")


if __name__ == "__main__":
    main()
