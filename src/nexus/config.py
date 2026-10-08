import os
from functools import cache
from pathlib import Path
from typing import Any, Optional

ROOT_PATH = Path(__file__).parent.parent.parent
SERVICES_PATH = ROOT_PATH / "services"
TERRAFORM_PATH = ROOT_PATH / "terraform"
TOFU_PATH = TERRAFORM_PATH
ANSIBLE_PATH = ROOT_PATH / "ansible"
VAULT_PATH = ANSIBLE_PATH / "vars" / "vault.yml"
TAILSCALE_PATH = ROOT_PATH / "tailscale"


def _find_private_root() -> Optional[Path]:
    """Discover the root path of the private repository, if available."""
    candidates = [
        os.environ.get("NEXUS_PRIVATE_PATH"),
        str(ROOT_PATH.parent / "nexus-private"),
        str(ROOT_PATH / ".private"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return Path(candidate).resolve()
    return None


PRIVATE_ROOT_PATH: Optional[Path] = _find_private_root()
PRIVATE_SERVICES_PATH: Optional[Path] = (
    PRIVATE_ROOT_PATH / "services"
    if PRIVATE_ROOT_PATH and (PRIVATE_ROOT_PATH / "services").is_dir()
    else None
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


PRESETS_PATH = ROOT_PATH / "config" / "presets.yml"


@cache
def load_presets() -> dict[str, list[str] | dict[str, Any]]:
    """Load presets from presets.yml file and optional private presets.

    Returns:
        Dictionary mapping preset names to their configuration.
        Configuration can be a list of service names or a dict with
        'extends' (str) and 'services' (list[str]) keys.

    Raises:
        FileNotFoundError: If presets.yml doesn't exist.
    """
    import yaml

    if not PRESETS_PATH.exists():
        raise FileNotFoundError(f"Presets file not found: {PRESETS_PATH}")

    with open(PRESETS_PATH) as f:
        presets: dict[str, Any] = yaml.safe_load(f) or {}

    if PRIVATE_ROOT_PATH:
        private_presets_path = PRIVATE_ROOT_PATH / "config" / "presets.yml"
        if private_presets_path.exists():
            with open(private_presets_path) as f:
                private_presets: dict[str, Any] = yaml.safe_load(f) or {}
            for name, config in private_presets.items():
                if name not in presets:
                    presets[name] = config
                else:
                    base = presets[name]
                    if isinstance(base, dict) and isinstance(config, dict):
                        merged = dict(base)
                        if "extends" in config:
                            merged["extends"] = config["extends"]
                        base_svcs = list(base.get("services", []))
                        priv_svcs = list(config.get("services", []))
                        for s in priv_svcs:
                            if s not in base_svcs:
                                base_svcs.append(s)
                        merged["services"] = base_svcs
                        presets[name] = merged
                    elif isinstance(base, list) and isinstance(config, list):
                        merged_list = list(base)
                        for s in config:
                            if s not in merged_list:
                                merged_list.append(s)
                        presets[name] = merged_list
                    elif isinstance(base, dict) and isinstance(config, list):
                        merged = dict(base)
                        base_svcs = list(base.get("services", []))
                        for s in config:
                            if s not in base_svcs:
                                base_svcs.append(s)
                        merged["services"] = base_svcs
                        presets[name] = merged
                    else:
                        presets[name] = config

    return presets


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
