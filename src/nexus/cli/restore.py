import logging
from typing import Optional

import click

from nexus.restore.backup import (
    _get_container_names,
    restore_backup,
)
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
@click.option(
    "--service",
    multiple=True,
    help="Service to restore (repeatable). Omit for all.",
)
@click.option("--snapshot", default="latest", help="Snapshot ID (default: latest).")
@click.option(
    "--target",
    type=click.Choice(["local", "r2"]),
    default="local",
    help="Repository to restore from.",
)
@click.option("--dry-run", is_flag=True, help="Preview restore without executing.")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def main(
    service: tuple[str, ...],
    snapshot: str,
    target: str,
    dry_run: bool,
    yes: bool,
) -> None:
    """Restore Nexus services from restic backup snapshots.

    Stops affected containers, restores data from a restic snapshot, then
    restarts containers. Use --service to limit the restore to specific
    services; omit it to restore all services.

    Args:
        service: Services to restore. Repeatable (e.g. --service foo --service bar).
        snapshot: Snapshot ID to restore from. Defaults to "latest".
        target: Repository target ("local" or "r2").
        dry_run: Preview operations without executing.
        yes: Skip the confirmation prompt.
    """
    services: Optional[list[str]] = list(service) if service else None

    if not dry_run and not yes:
        affected = services or ["all services"]
        print(f"\nAbout to restore from snapshot '{snapshot}' (repo: {target})")
        print(f"Services: {', '.join(affected)}")
        if services:
            containers: list[str] = []
            for svc in services:
                containers.extend(_get_container_names(svc))
            if containers:
                print(f"Containers that will stop: {', '.join(containers)}")
        click.confirm("\nProceed with restore?", abort=True)

    restore_backup(
        snapshot_id=snapshot,
        services=services,
        target=target,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    main()
