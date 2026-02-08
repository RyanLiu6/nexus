import os
from functools import cache
from pathlib import Path
from typing import Optional

ROOT_PATH = Path(__file__).parent.parent.parent
SERVICES_PATH = ROOT_PATH / "services"
TERRAFORM_PATH = ROOT_PATH / "terraform"
ANSIBLE_PATH = ROOT_PATH / "ansible"
VAULT_PATH = ANSIBLE_PATH / "vars" / "vault.yml"
TAILSCALE_PATH = ROOT_PATH / "tailscale"
BACKUP_DIR = (
    Path(os.environ.get("NEXUS_DATA_DIRECTORY", "~/Data")).expanduser() / "Backups"
)


@cache
def get_all_services() -> list[str]:
    """Get all available service names from manifest discovery.

    Returns:
        Sorted list of service names that have valid service.yml manifests.
    """
    # Import here to avoid circular imports
    from nexus.services import get_all_service_names

    return get_all_service_names()


PRESETS = {
    "core": ["traefik", "tailscale-access", "dashboard", "monitoring", "vaultwarden"],
    "home": ["core", "backups", "sure", "foundryvtt", "jellyfin", "transmission"],
}


def resolve_preset(name: str) -> list[str]:
    """Resolve a preset name to its list of services, handling nested presets.

    Recursively expands presets that reference other presets to build the
    complete list of services.

    Args:
        name: The name of the preset to resolve.

    Returns:
        A deduplicated list of service names included in the preset.
    """
    services = []
    for item in PRESETS.get(name, []):
        if item in PRESETS:
            services.extend(resolve_preset(item))
        else:
            services.append(item)
    return list(set(services))


def get_base_domain() -> Optional[str]:
    """Retrieve the base domain from the NEXUS_DOMAIN environment variable.

    Returns:
        The base domain string if the environment variable is set,
        None if not configured.
    """
    return os.environ.get("NEXUS_DOMAIN")
