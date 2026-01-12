import logging
from pathlib import Path
from typing import Optional

from nexus.config import BACKUP_DIR, ROOT_PATH
from nexus.utils import run_command

logger = logging.getLogger(__name__)


def list_backups() -> list[Path]:
    """List available backups.

    Returns:
        A list of paths to backup files, sorted by newest first.
    """
    if not BACKUP_DIR.exists():
        logger.error(f"Backup directory not found: {BACKUP_DIR}")
        return []

    backups = sorted(BACKUP_DIR.glob("*.tar.gz"), reverse=True)
    return backups


def restore_backup(
    backup_path: Path, services: Optional[list[str]] = None, dry_run: bool = False
) -> None:
    """Restore from backup file.

    Args:
        backup_path: Path to the backup file.
        services: List of specific services to restore. If None, restores all.
        dry_run: If True, do not execute the restore command.
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
    """Restore database from SQL file.

    Args:
        service: The name of the service to restore the database for.
        sql_file: Path to the SQL file.
        dry_run: If True, do not execute the restore command.

    Raises:
        NotImplementedError: If database restore is not implemented for the service.
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
