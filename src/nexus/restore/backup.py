import json
import logging
from pathlib import Path
from typing import Any, Optional

from nexus.config import ROOT_PATH
from nexus.utils import run_command

logger = logging.getLogger(__name__)


def get_backrest_config() -> dict[str, Any]:
    """Retrieve and parse the Backrest configuration from the running container.

    Reads the Backrest configuration JSON file from inside the backrest Docker
    container, which serves as the single source of truth for repo URIs and
    retention policies.

    Returns:
        Parsed configuration dict with structure:
        {"repos": [{"id": str, "uri": str, ...}],
         "plans": [{"id": str, "repo": str,
                    "retention": {"policyKeepLastN": int}, ...}]}

    Raises:
        RuntimeError: If the docker exec command fails or output cannot be
            parsed as JSON.
    """
    try:
        result = run_command(
            ["docker", "exec", "backrest", "cat", "/config/config.json"]
        )
        return dict(json.loads(result.stdout))
    except Exception as e:
        raise RuntimeError(f"Failed to read Backrest config: {e}") from e


def push_backup(target: str = "all", dry_run: bool = False) -> None:
    """Trigger a restic backup and prune for the specified target repositories.

    Reads repo URIs and retention policies from the Backrest config, then runs
    `restic backup /userdata` followed by `restic forget --keep-last N --prune`
    for each targeted plan. Keeps manual and scheduled backups consistent.

    Args:
        target: Which repositories to back up. One of "local", "r2", or "all".
            Defaults to "all".
        dry_run: If True, log the commands without executing them.

    Raises:
        ValueError: If target is not one of "local", "r2", or "all".
        RuntimeError: If the Backrest config cannot be read.
    """
    if target not in ("local", "r2", "all"):
        raise ValueError(f"Invalid target '{target}'. Must be 'local', 'r2', or 'all'.")

    config = get_backrest_config()

    repos_by_id = {repo["id"]: repo for repo in config.get("repos", [])}
    plans = config.get("plans", [])

    for plan in plans:
        repo_id = plan.get("repo", "")

        if target != "all" and repo_id != target:
            continue

        repo = repos_by_id.get(repo_id)
        if not repo:
            logger.warning(
                f"Repo '{repo_id}' not found in config, "
                f"skipping plan '{plan.get('id')}'"
            )
            continue

        uri = repo["uri"]
        keep_last = plan.get("retention", {}).get("policyKeepLastN", 1)
        plan_id = plan.get("id", repo_id)

        backup_cmd = [
            "docker",
            "exec",
            "backrest",
            "restic",
            "-r",
            uri,
            "backup",
            "/userdata",
        ]
        forget_cmd = [
            "docker",
            "exec",
            "backrest",
            "restic",
            "-r",
            uri,
            "forget",
            "--keep-last",
            str(keep_last),
            "--prune",
        ]

        if dry_run:
            logger.info(
                f"[DRY RUN] Plan '{plan_id}': would run: {' '.join(backup_cmd)}"
            )
            logger.info(
                f"[DRY RUN] Plan '{plan_id}': would run: {' '.join(forget_cmd)}"
            )
            continue

        logger.info(f"Backing up plan '{plan_id}' to repo '{repo_id}' ({uri})")
        run_command(backup_cmd)
        logger.info(f"Pruning plan '{plan_id}' (keep-last={keep_last})")
        run_command(forget_cmd)
        logger.info(f"Plan '{plan_id}' backup complete")


def list_backups() -> list[str]:
    """Retrieve all available backup snapshots from restic repositories.

    Uses `docker exec backrest restic snapshots --json` to get snapshot IDs.

    Returns:
        List of snapshot IDs (strings). Empty list if no snapshots found
        or command fails.
    """
    try:
        result = run_command(
            [
                "docker",
                "exec",
                "backrest",
                "restic",
                "-r",
                "/repos",
                "snapshots",
                "--json",
            ]
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
        "-r",
        "/repos",
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
