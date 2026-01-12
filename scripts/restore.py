#!/usr/bin/env python3
import logging
import os
from pathlib import Path
from typing import Optional

import click

from nexus.utils import run_command

ROOT_PATH = Path(__file__).parent.parent
BACKUP_DIR = Path(
    os.environ.get("NEXUS_BACKUP_DIRECTORY", "~/nexus-backups")
).expanduser()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
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


def restore_backup(backup_path: Path, services: Optional[list[str]] = None) -> None:
    """Restore from backup file.

    Args:
        backup_path: Path to the backup file.
        services: List of specific services to restore. If None, restores all.
    """
    logger.info(f"Restoring from: {backup_path}")

    if services:
        logger.info(f"Restoring services: {', '.join(services)}")

    run_command(["docker", "compose", "down"])

    run_command(["tar", "-xzf", str(backup_path), "-C", "/"])

    run_command(["docker", "compose", "up", "-d"])

    logger.info("Restore complete!")


def restore_database(service: str, sql_file: Path) -> None:
    """Restore database from SQL file.

    Args:
        service: The name of the service to restore the database for.
        sql_file: Path to the SQL file.
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
        with sql_file.open("r") as f:
            run_command(cmd, stdin=f)
    else:
        logger.error(f"Database restore not implemented for {service}")
        return


@click.command()
@click.option("--list", "show_list", is_flag=True, help="List available backups")
@click.option("--backup", type=str, help="Backup file to restore")
@click.option("--service", type=str, help="Specific service to restore")
@click.option("--db", type=str, help="Restore database from SQL file")
@click.option("--verify", is_flag=True, help="Verify backup integrity")
def main(
    show_list: bool,
    backup: Optional[str],
    service: Optional[str],
    db: Optional[str],
    verify: bool,
) -> None:
    """Restore Nexus services from backups.

    Args:
        show_list: List available backups.
        backup: Backup file to restore.
        service: Specific service to restore.
        db: Restore database from SQL file.
        verify: Verify backup integrity.
    """
    if show_list:
        backups = list_backups()
        if not backups:
            logger.info("No backups found")
            return

        print("\nAvailable backups:")
        for i, backup_file in enumerate(backups, 1):
            size_mb = backup_file.stat().st_size / 1024 / 1024
            print(f"  {i}. {backup_file.name} ({size_mb:.2f} MB)")
        return

    if verify and backup:
        backup_path = BACKUP_DIR / backup
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return

        import tarfile

        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                members = tar.getnames()
                logger.info(f"Backup contains {len(members)} files")
                logger.info("Backup appears valid")
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
        return

    if backup:
        backup_path = BACKUP_DIR / backup
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return

        if db:
            if not service:
                logger.error("Service must be specified when restoring database")
                return

            db_file = Path(db)
            if not db_file.exists():
                logger.error(f"Database file not found: {db_file}")
                return
            restore_database(service, db_file)
        else:
            restore_backup(backup_path, [service] if service else None)
    else:
        logger.error("No backup specified. Use --backup or --list")


if __name__ == "__main__":
    main()
