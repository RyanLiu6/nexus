import os
from pathlib import Path
from typing import Optional

ROOT_PATH = Path(__file__).parent.parent.parent
SERVICES_PATH = ROOT_PATH / "services"
TERRAFORM_PATH = ROOT_PATH / "terraform"
ANSIBLE_PATH = ROOT_PATH / "ansible"
BACKUP_DIR = Path(
    os.environ.get("NEXUS_BACKUP_DIRECTORY", "~/nexus-backups")
).expanduser()

ALL_SERVICES = sorted([d.name for d in SERVICES_PATH.iterdir() if d.is_dir()])

PRESETS = {
    "core": ["traefik", "auth", "dashboard", "monitoring"],
    "home": ["core", "backups", "sure", "foundryvtt", "jellyfin", "transmission"],
}


def resolve_preset(name: str) -> list[str]:
    """Resolve preset with inheritance.

    Args:
        name: The name of the preset to resolve.

    Returns:
        A list of service names included in the preset.
    """
    services = []
    for item in PRESETS.get(name, []):
        if item in PRESETS:
            services.extend(resolve_preset(item))
        else:
            services.append(item)
    return list(set(services))


def get_base_domain() -> Optional[str]:
    """Get base domain from NEXUS_DOMAIN environment variable.

    Returns:
        The base domain if found, None otherwise.
    """
    return os.environ.get("NEXUS_DOMAIN")
