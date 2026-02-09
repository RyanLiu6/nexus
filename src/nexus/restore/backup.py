import json
import logging
from pathlib import Path
from typing import Optional

from nexus.config import ROOT_PATH
from nexus.utils import run_command

logger = logging.getLogger(__name__)


def list_backups() -> list[str]:
    """Retrieve all available backup snapshots from restic repositories.

    Uses `docker exec backrest restic snapshots --json` to get snapshot IDs.

    Returns:
        List of snapshot IDs (strings). Empty list if no snapshots found
        or command fails.
    """
    try:
        result = run_command(
            ["docker", "exec", "backrest", "restic", "snapshots", "--json"]
        )
        snapshots_data = json.loads(result.stdout)
        snapshots = [snapshot["short_id"] for snapshot in snapshots_data]
        return snapshots
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        return []


def restore_backup(
    snapshot_id: str, services: Optional[list[str]] = None, dry_run: bool = False
) -> None:
    """Restore services from a restic backup snapshot.

    Extracts the specified snapshot using restic, optionally filtering
    by service paths.

    Args:
        snapshot_id: ID of the backup snapshot to restore from.
        services: Optional list of specific services to restore.
            If provided, only restores /userdata/<service> paths.
        dry_run: If True, log the restoration steps without executing.
    """
    logger.info(f"Restoring from snapshot: {snapshot_id}")

    if services:
        logger.info(f"Restoring services: {', '.join(services)}")

    cmd = [
        "docker",
        "exec",
        "backrest",
        "restic",
        "restore",
        snapshot_id,
        "--target",
        "/tmp/restore",
    ]

    if services:
        for service in services:
            cmd.extend(["--include", f"/userdata/{service}"])

    if dry_run:
        logger.info("[DRY RUN] Would restore services from backup")
        logger.info(f"[DRY RUN] Snapshot: {snapshot_id}")
        logger.info(f"[DRY RUN] Would run: {' '.join(cmd)}")
        return

    run_command(cmd)

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
