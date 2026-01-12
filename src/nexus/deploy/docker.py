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
    """Run docker compose command for a service.

    Args:
        service_path: Path to the service directory.
        action: Docker compose action (up, down, ps, logs, etc.).
        extra_args: Additional arguments for the command.
        dry_run: If True, do not execute the command.

    Returns:
        The completed process object.

    Raises:
        FileNotFoundError: If the service path does not exist.
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
