import logging
from pathlib import Path
from typing import Optional

import click

from nexus.config import BACKUP_DIR
from nexus.restore.backup import list_backups, restore_backup, restore_database

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _verify_backup(backup_path: Path) -> bool:
    import tarfile

    try:
        with tarfile.open(backup_path, "r:gz") as tar:
            members = tar.getnames()
            logger.info(f"Backup contains {len(members)} files")
            logger.info("Backup appears valid")
            return True
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        return False


@click.command()
@click.option("--list", "show_list", is_flag=True, help="List available backups.")
@click.option("--backup", type=str, help="Backup file to restore.")
@click.option("--service", type=str, help="Specific service to restore.")
@click.option("--db", type=str, help="Restore database from SQL file.")
@click.option("--verify", is_flag=True, help="Verify backup integrity.")
@click.option("--dry-run", is_flag=True, help="Preview restore without executing.")
def main(
    show_list: bool,
    backup: Optional[str],
    service: Optional[str],
    db: Optional[str],
    verify: bool,
    dry_run: bool,
) -> None:
    """Restore Nexus services from backups."""
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

        _verify_backup(backup_path)
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
            restore_database(service, db_file, dry_run)
        else:
            restore_backup(backup_path, [service] if service else None, dry_run)
    else:
        logger.error("No backup specified. Use --backup or --list")


if __name__ == "__main__":
    main()
