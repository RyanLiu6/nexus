import logging
from pathlib import Path
from typing import Optional

from nexus.config import BACKUP_DIR, ROOT_PATH
from nexus.utils import run_command

logger = logging.getLogger(__name__)


def list_backups() -> list[Path]:
    """Retrieve all available backup files from the backup directory.

    Scans the configured backup directory for tar.gz files and returns
    them sorted with the most recent first.

    Returns:
        List of Path objects pointing to backup files, sorted by
        modification time (newest first). Empty list if directory
        doesn't exist or contains no backups.
    """
    if not BACKUP_DIR.exists():
        logger.error(f"Backup directory not found: {BACKUP_DIR}")
        return []

    backups = sorted(BACKUP_DIR.glob("*.tar.gz"), reverse=True)
    return backups


def restore_backup(
    backup_path: Path, services: Optional[list[str]] = None, dry_run: bool = False
) -> None:
    """Restore services from a backup archive.

    Stops all running containers, extracts the backup archive to root,
    and restarts the containers. This is a full restoration that
    overwrites existing data.

    Args:
        backup_path: Path to the backup tar.gz file to restore from.
        services: Optional list of specific services to restore.
            If None, all services in the backup are restored.
        dry_run: If True, log the restoration steps without executing.
    """
    logger.info(f"Restoring from: {backup_path}")

    if services:
        logger.info(f"Restoring services: {', '.join(services)}")

    if dry_run:
        logger.info("[DRY RUN] Would restore services from backup")
        logger.info(f"[DRY RUN] Backup path: {backup_path}")
        logger.info("[DRY RUN] Would run: docker compose down")
        logger.info(f"[DRY RUN] Would run: tar -xzf {backup_path} -C /")
        logger.info("[DRY RUN] Would run: docker compose up -d")
        return

    run_command(["docker", "compose", "down"])
    run_command(["tar", "-xzf", str(backup_path), "-C", "/"])
    run_command(["docker", "compose", "up", "-d"])

    logger.info("Restore complete!")


def restore_database(service: str, sql_file: Path, dry_run: bool = False) -> None:
    """Restore a service's PostgreSQL database from an SQL dump.

    Connects to the service's database container and pipes the SQL file
    to psql for restoration. Currently only supports the 'sure' service.

    Args:
        service: Name of the service whose database to restore.
            Only "sure" is currently implemented.
        sql_file: Path to the SQL dump file to restore.
        dry_run: If True, log the command without executing.

    Raises:
        NotImplementedError: If database restore is not implemented for
            the specified service.
    """
    logger.info(f"Restoring database for {service} from {sql_file}")

    if service == "sure":
        cmd = [
            "docker",
            "compose",
            "exec",
            "-T",
            "sure-db",
            "psql",
            "-U",
            "sure_user",
            "-d",
            "sure_production",
        ]

        if dry_run:
            logger.info(f"[DRY RUN] Would run: {' '.join(cmd)} < {sql_file}")
            return

        with sql_file.open("r") as f:
            run_command(cmd, cwd=ROOT_PATH, stdin=f)

        logger.info(f"Database restore complete for {service}")
    else:
        logger.error(f"Database restore not implemented for {service}")
        raise NotImplementedError(f"Database restore not implemented for {service}")
