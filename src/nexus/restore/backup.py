import json
import logging
import os
from typing import Any, Optional

import yaml

from nexus.config import SERVICES_PATH
from nexus.utils import read_vault, run_command

logger = logging.getLogger(__name__)

CONFIG_DIR_OVERRIDES = {"backups": "backrest"}

BACKREST_IMAGE = "ghcr.io/garethgeorge/backrest:latest"


def _get_config_dir_name(service_name: str) -> str:
    return CONFIG_DIR_OVERRIDES.get(service_name, service_name)


def _get_container_names(service_name: str) -> list[str]:
    """Parse a service's docker-compose.yml to extract container names.

    Args:
        service_name: Name of the service directory under services/.

    Returns:
        List of container_name values defined in the compose file.
        Returns empty list if the compose file doesn't exist.
    """
    compose_path = SERVICES_PATH / service_name / "docker-compose.yml"
    if not compose_path.exists():
        return []
    with open(compose_path) as f:
        compose = yaml.safe_load(f)
    services = compose.get("services", {})
    return [
        svc_config.get("container_name", name) for name, svc_config in services.items()
    ]


def _get_restore_config() -> tuple[str, str]:
    """Read NEXUS_DATA_DIRECTORY and RESTIC_PASSWORD from vault.

    Falls back to environment variables if vault is unavailable or keys
    are missing.

    Returns:
        Tuple of (data_directory, restic_password).
    """
    data_dir = os.environ.get("NEXUS_DATA_DIRECTORY", "")
    password = os.environ.get("RESTIC_PASSWORD", "")

    if not data_dir or not password:
        try:
            vault = read_vault()
            if not data_dir:
                data_dir = vault.get("nexus_data_directory", "")
            if not password:
                password = vault.get("restic_password", "")
        except Exception as e:
            logger.warning(f"Could not read vault: {e}")

    return (data_dir, password)


def _get_all_backup_services() -> list[str]:
    """Discover all services that have a docker-compose.yml.

    Returns:
        Sorted list of service names.
    """
    return sorted(
        d.name
        for d in SERVICES_PATH.iterdir()
        if d.is_dir() and (d / "docker-compose.yml").exists()
    )


def _build_ephemeral_cmd(
    data_dir: str,
    password: str,
    uri: str,
    target: str,
    extra_mounts: Optional[list[str]] = None,
) -> list[str]:
    cmd = [
        "docker",
        "run",
        "--rm",
        "--entrypoint",
        "restic",
        "-v",
        f"{data_dir}/Backups:/repos:ro",
        "-e",
        f"RESTIC_PASSWORD={password}",
    ]
    if target == "r2":
        cmd.extend(
            [
                "-v",
                f"{data_dir}/Config/backrest/rclone:/root/.config/rclone:ro",
            ]
        )
    if extra_mounts:
        for mount in extra_mounts:
            cmd.extend(["-v", mount])
    # --no-lock: repos mount is :ro so restic cannot write a lock file
    cmd.extend([BACKREST_IMAGE, "--no-lock", "-r", uri])
    return cmd


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
            ["docker", "exec", "backrest", "cat", "/config/config.json"],
            capture=True,
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


def list_backups(target: str = "local") -> list[dict[str, str]]:
    """List snapshots from a restic repository.

    Uses an ephemeral docker container instead of docker exec into the running
    backrest container, so vault secrets are used directly.

    Args:
        target: Which repository to list snapshots from. One of "local" or "r2".

    Returns:
        List of dicts with 'id', 'short_id', 'time' keys.
        Returns empty list on error.
    """
    try:
        data_dir, password = _get_restore_config()
        config = get_backrest_config()
        repos_by_id = {repo["id"]: repo for repo in config.get("repos", [])}
        repo = repos_by_id.get(target)
        if not repo:
            logger.error(f"Repo '{target}' not found in Backrest config")
            return []

        uri = repo["uri"]
        cmd = _build_ephemeral_cmd(data_dir, password, uri, target)
        cmd.extend(["snapshots", "--json"])

        result = run_command(cmd, capture=True)
        snapshots_data = json.loads(result.stdout)
        return [
            {"id": s["id"], "short_id": s["short_id"], "time": s["time"]}
            for s in snapshots_data
        ]
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        return []


def restore_backup(
    snapshot_id: str = "latest",
    services: Optional[list[str]] = None,
    target: str = "local",
    dry_run: bool = False,
) -> None:
    """Restore services from a restic backup snapshot.

    Stops affected containers, restores files via an ephemeral restic container,
    then restarts containers. The start step runs in a finally block to ensure
    containers are always brought back up.

    Args:
        snapshot_id: ID of the backup snapshot to restore from. Use "latest"
            to automatically resolve the most recent snapshot.
        services: Optional list of specific service names to restore.
            If None, restores all discovered services.
        target: Which repository to restore from. One of "local" or "r2".
        dry_run: If True, log the restoration steps without executing.

    Raises:
        ValueError: If the target repo is not found in Backrest config.
        RuntimeError: If snapshot resolution or restore fails.
    """
    data_dir, password = _get_restore_config()

    config = get_backrest_config()
    repos_by_id = {repo["id"]: repo for repo in config.get("repos", [])}
    repo = repos_by_id.get(target)
    if not repo:
        raise ValueError(f"Repo '{target}' not found in Backrest config")
    uri = repo["uri"]

    if snapshot_id == "latest":
        snapshot_id = _resolve_latest_snapshot(data_dir, password, uri, target)
        logger.info(f"Resolved latest snapshot: {snapshot_id}")

    affected_services = services or _get_all_backup_services()

    containers: list[str] = []
    for svc in affected_services:
        containers.extend(_get_container_names(svc))

    restore_cmd = _build_ephemeral_cmd(
        data_dir,
        password,
        uri,
        target,
        extra_mounts=[f"{data_dir}/Config:/userdata:rw"],
    )
    restore_cmd.extend(["restore", snapshot_id, "--target", "/"])
    if services:
        for svc in services:
            restore_cmd.extend(["--include", f"/userdata/{_get_config_dir_name(svc)}"])

    if dry_run:
        logger.info(f"[DRY RUN] Snapshot: {snapshot_id}")
        if containers:
            logger.info(f"[DRY RUN] Would stop containers: {' '.join(containers)}")
        logger.info(f"[DRY RUN] Would run: {' '.join(restore_cmd)}")
        if containers:
            logger.info(f"[DRY RUN] Would start containers: {' '.join(containers)}")
        return

    if containers:
        logger.info(f"Stopping containers: {' '.join(containers)}")
        run_command(["docker", "stop", *containers])

    try:
        logger.info(f"Restoring snapshot {snapshot_id} from '{target}' repo")
        run_command(restore_cmd)
        logger.info("Restore complete!")
    finally:
        if containers:
            logger.info(f"Starting containers: {' '.join(containers)}")
            run_command(["docker", "start", *containers])


def _resolve_latest_snapshot(
    data_dir: str, password: str, uri: str, target: str
) -> str:
    """Resolve 'latest' to an actual snapshot ID.

    Args:
        data_dir: Path to the nexus data directory.
        password: Restic repository password.
        uri: Repository URI.
        target: Repository target ("local" or "r2").

    Returns:
        The full snapshot ID string.

    Raises:
        RuntimeError: If no snapshots are found in the repository.
    """
    cmd = _build_ephemeral_cmd(data_dir, password, uri, target)
    cmd.extend(["snapshots", "--json", "--latest", "1"])
    result = run_command(cmd, capture=True)
    snapshots = json.loads(result.stdout)
    if not snapshots:
        raise RuntimeError("No snapshots found in repository")
    return str(snapshots[0]["id"])
