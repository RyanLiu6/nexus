from pathlib import Path

import yaml
from pyinfra import logger
from pyinfra.operations import files

# =============================================================================
# Load Secrets
# =============================================================================
# For now, we will load from the unencrypted config/secrets.yml to transition.
# Eventually this will load from config/secrets.enc.yml via SOPS.
SECRETS_PATH = Path("config/secrets.yml")


def load_secrets():
    """Load secrets from the unencrypted YAML file."""
    if not SECRETS_PATH.exists():
        logger.error(f"Secrets file not found at {SECRETS_PATH}")
        return {}
    with open(SECRETS_PATH) as f:
        return yaml.safe_load(f)


secrets = load_secrets()
NEXUS_ROOT = secrets.get("nexus_root_directory", str(Path.cwd()))
NEXUS_DATA = secrets.get("nexus_data_directory", "/Volumes/Data")

logger.info(f"Loaded configuration for {secrets.get('nexus_domain')}")

# =============================================================================
# Base Directories
# =============================================================================
directories = [
    NEXUS_DATA,
    f"{NEXUS_DATA}/Config",
    f"{NEXUS_DATA}/Config/traefik",
]

for d in directories:
    files.directory(
        name=f"Ensure directory exists: {d}",
        path=d,
        present=True,
    )

# Note: The rest of the docker-compose deployment logic will be ported here.
