import logging
import subprocess
from pathlib import Path
from typing import Optional

from nexus.utils import run_command


def run_docker_compose(
    service_path: Path,
    action: str = "up",
    extra_args: Optional[list[str]] = None,
    dry_run: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Execute a docker compose command for a specific service.

    Runs docker compose with the specified action in the service's directory.
    Supports common actions like up, down, ps, and logs with optional arguments.

    Args:
        service_path: Path to the service directory containing docker-compose.yml.
        action: Docker compose action to execute. Supported values:
            "up" (starts in detached mode), "down", "ps", "logs", or any other
            valid docker compose command.
        extra_args: Additional command-line arguments to pass to docker compose.
        dry_run: If True, log the command without executing it.

    Returns:
        The subprocess.CompletedProcess result from the docker compose command.

    Raises:
        FileNotFoundError: If the service_path directory does not exist.
    """
    if not service_path.exists():
        raise FileNotFoundError(f"Service path not found: {service_path}")

    cmd = ["docker", "compose"]
    if action == "up":
        cmd.extend(["up", "-d"])
    elif action == "down":
        cmd.append("down")
    elif action == "ps":
        cmd.append("ps")
    elif action == "logs":
        cmd.append("logs")
    else:
        cmd.append(action)

    if extra_args:
        cmd.extend(extra_args)

    if dry_run:
        logging.info(f"[DRY RUN] Would run: {' '.join(cmd)}")
        logging.info(f"[DRY RUN] Working directory: {service_path}")
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    logging.debug(f"Running docker compose in {service_path}")
    return run_command(cmd, cwd=service_path)
