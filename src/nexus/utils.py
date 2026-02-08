import logging
import subprocess
from pathlib import Path
from typing import Any, Optional, TextIO, Union

import yaml

from nexus.config import ROOT_PATH, VAULT_PATH


def run_command(
    command: list[str],
    cwd: Optional[Path] = None,
    capture: bool = False,
    check: bool = True,
    stdin: Optional[Union[TextIO, int]] = None,
) -> subprocess.CompletedProcess[str]:
    """Execute a shell command with standardized error handling and logging.

    Provides a wrapper around subprocess.run with consistent behavior across
    the codebase, including debug logging and proper error propagation.

    Args:
        command: The command to run as a list of strings (e.g., ["docker", "ps"]).
        cwd: The working directory for the command. Defaults to ROOT_PATH.
        capture: If True, capture stdout/stderr into the result object.
        check: If True, raise CalledProcessError on non-zero exit code.
        stdin: File object or file descriptor to use as stdin for piping input.

    Returns:
        The subprocess.CompletedProcess object containing return code and output.

    Raises:
        subprocess.CalledProcessError: If the command fails and check is True.
    """
    logging.debug(f"Running: {' '.join(command)} in {cwd or ROOT_PATH}")

    try:
        result = subprocess.run(
            command,
            cwd=cwd or ROOT_PATH,
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


def read_vault(vault_path: Optional[Path] = None) -> dict[str, Any]:
    """Read and decrypt the Ansible vault file.

    Uses ansible-vault to decrypt the vault.yml file and parse its contents.
    Requires ansible-vault to be installed and the vault password to be
    available (via --ask-vault-pass prompt or ANSIBLE_VAULT_PASSWORD_FILE).

    Args:
        vault_path: Path to the vault file. Defaults to VAULT_PATH.

    Returns:
        Dictionary containing the decrypted vault contents.
        Structure matches the vault.yml schema (mixed types).

    Raises:
        FileNotFoundError: If the vault file does not exist.
        subprocess.CalledProcessError: If ansible-vault decryption fails.
        yaml.YAMLError: If the vault contents are not valid YAML.
    """
    path = vault_path or VAULT_PATH

    if not path.exists():
        raise FileNotFoundError(f"Vault file not found: {path}")

    # Check if vault is encrypted
    with open(path) as f:
        first_line = f.readline()

    if first_line.startswith("$ANSIBLE_VAULT"):
        # Encrypted - use ansible-vault to decrypt
        logging.debug(f"Decrypting vault: {path}")
        result = run_command(
            ["ansible-vault", "view", str(path)],
            capture=True,
        )
        vault_content = result.stdout
    else:
        # Unencrypted (development mode)
        logging.debug(f"Reading unencrypted vault: {path}")
        with open(path) as f:
            vault_content = f.read()

    parsed: dict[str, Any] = yaml.safe_load(vault_content)
    return parsed
