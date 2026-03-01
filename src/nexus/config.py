import os
from functools import cache
from pathlib import Path
from typing import Any, Optional

ROOT_PATH = Path(__file__).parent.parent.parent
SERVICES_PATH = ROOT_PATH / "services"
TERRAFORM_PATH = ROOT_PATH / "terraform"
ANSIBLE_PATH = ROOT_PATH / "ansible"
VAULT_PATH = ANSIBLE_PATH / "vars" / "vault.yml"
TAILSCALE_PATH = ROOT_PATH / "tailscale"


@cache
def get_all_services() -> list[str]:
    """Get all available service names from manifest discovery.

    Returns:
        Sorted list of service names that have valid service.yml manifests.
    """
    # Import here to avoid circular imports
    from nexus.services import get_all_service_names

    return get_all_service_names()


PRESETS_PATH = ROOT_PATH / "config" / "presets.yml"


@cache
def load_presets() -> dict[str, list[str] | dict[str, Any]]:
    """Load presets from presets.yml file.

    Returns:
        Dictionary mapping preset names to their configuration.
        Configuration can be a list of service names or a dict with
        'extends' (str) and 'services' (list[str]) keys.

    Raises:
        FileNotFoundError: If presets.yml doesn't exist.
    """
    import yaml

    with open(PRESETS_PATH) as f:
        return yaml.safe_load(f) or {}


def resolve_preset(name: str) -> list[str]:
    """Resolve a preset name to its list of services, handling extends.

    Supports the 'extends' key for preset inheritance.

    Args:
        name: The name of the preset to resolve.

    Returns:
        A deduplicated list of service names included in the preset.
    """
    presets = load_presets()
    preset = presets.get(name)

    if preset is None:
        return []

    services: list[str] = []

    # Handle dict format with 'extends' and 'services' keys
    if isinstance(preset, dict):
        if "extends" in preset:
            services.extend(resolve_preset(preset["extends"]))
        services.extend(preset.get("services", []))
    # Handle simple list format
    elif isinstance(preset, list):
        for item in preset:
            if item in presets:
                services.extend(resolve_preset(item))
            else:
                services.append(item)

    return sorted(list(set(services)))


def get_base_domain() -> Optional[str]:
    """Retrieve the base domain from the NEXUS_DOMAIN environment variable.

    Returns:
        The base domain string if the environment variable is set,
        None if not configured.
    """
    return os.environ.get("NEXUS_DOMAIN")


# Export for CLI
try:
    PRESETS = load_presets()
except FileNotFoundError:
    PRESETS = {}
