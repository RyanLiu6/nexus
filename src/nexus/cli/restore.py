import logging
from pathlib import Path
from typing import Optional

import click

from nexus.restore.backup import list_backups, restore_backup, restore_database
from nexus.utils import run_command

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _verify_backup() -> bool:
    try:
        run_command(["docker", "exec", "backrest", "restic", "-r", "/repos", "check"])
        logger.info("Backup repositories verified successfully")
        return True
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        return False


@click.command()
@click.option("--list", "show_list", is_flag=True, help="List available backups.")
@click.option("--snapshot", type=str, help="Backup snapshot to restore.")
@click.option("--service", type=str, help="Specific service to restore.")
@click.option("--db", type=str, help="Restore database from SQL file.")
@click.option("--verify", is_flag=True, help="Verify backup integrity.")
@click.option("--dry-run", is_flag=True, help="Preview restore without executing.")
def main(
    show_list: bool,
    snapshot: Optional[str],
    service: Optional[str],
    db: Optional[str],
    verify: bool,
    dry_run: bool,
) -> None:
    """Restore Nexus services from restic backup snapshots.

    Lists available backups, verifies backup integrity, and restores service
    data or databases from backup snapshots. Supports full restores or targeting
    specific services.

    Args:
        show_list: Display available backup snapshots and exit.
        snapshot: ID of the backup snapshot to restore from.
        service: Limit restore to a specific service name.
        db: Path to SQL dump file for database restoration.
        verify: Validate backup integrity without restoring.
        dry_run: Preview restore operations without executing them.
    """
    if show_list:
        snapshots = list_backups()
        if not snapshots:
            logger.info("No backup snapshots found")
            return

        print("\nAvailable backup snapshots:")
        for i, snapshot_id in enumerate(snapshots, 1):
            print(f"  {i}. {snapshot_id}")
        return

    if verify:
        _verify_backup()
        return

    if not snapshot:
        snapshots = list_backups()
        if not snapshots:
            logger.error("No backup snapshots found")
            return

        print("\nAvailable backup snapshots:")
        for i, snapshot_id in enumerate(snapshots, 1):
            print(f"  {i}. {snapshot_id}")

        choice = click.prompt(
            "Select snapshot number",
            type=click.IntRange(1, len(snapshots)),
        )
        snapshot = snapshots[choice - 1]

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
        restore_backup(snapshot, [service] if service else None, dry_run)


if __name__ == "__main__":
    main()
