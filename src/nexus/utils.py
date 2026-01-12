import logging
import subprocess
from pathlib import Path
from typing import IO, Any, Optional, Union

from nexus.config import ROOT_PATH


def run_command(
    command: list[str],
    cwd: Optional[Path] = None,
    capture: bool = False,
    check: bool = True,
    stdin: Optional[Union[IO[Any], int]] = None,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command with error handling.

    Args:
        command: The command to run as a list of strings.
        cwd: The working directory for the command. Defaults to ROOT_PATH.
        capture: If True, capture stdout/stderr.
        check: If True, check the return code and raise CalledProcessError if non-zero.
        stdin: File object or file descriptor to use as stdin.

    Returns:
        The completed process object.

    Raises:
        subprocess.CalledProcessError: If the command fails and check is True.
    """
    if cwd is None:
        cwd = ROOT_PATH

    logging.debug(f"Running: {' '.join(command)} in {cwd}")

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture,
            text=True,
            check=check,
            stdin=stdin,
        )
        if capture and result.stdout:
            logging.debug(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {' '.join(command)}")
        if e.stderr:
            logging.error(f"Error: {e.stderr}")
        raise
