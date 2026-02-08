"""Access rules generator from service manifests.

Auto-generates tailscale/access-rules.yml from service.yml manifests.
"""

from pathlib import Path
from typing import Any, Optional

import yaml

from nexus.config import TAILSCALE_PATH
from nexus.services import discover_services
from nexus.utils import read_vault


def generate_access_rules(
    services: Optional[list[str]] = None,
    output_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Generate access rules from service manifests.

    Args:
        services: List of service names to include. If None, includes all.
        output_path: Path to write the generated rules. If None, returns dict only.

    Returns:
        Dictionary of generated access rules.
    """
    all_services = discover_services()

    # Filter to requested services if specified
    if services:
        manifests = [all_services[s] for s in services if s in all_services]
    else:
        manifests = list(all_services.values())

    # Get groups from vault
    try:
        vault = read_vault()
        groups_config = vault.get("tailscale_users", {})
    except (FileNotFoundError, KeyError):
        groups_config = {}

    # Build access rules
    rules: dict[str, Any] = {
        "groups": groups_config,
        "default": "deny",
        "services": {},
    }

    for manifest in manifests:
        # Skip services without web access or access groups
        if not manifest.access_groups:
            continue

        # Add entry for each subdomain
        for subdomain in manifest.subdomains:
            rules["services"][subdomain] = {
                "groups": manifest.access_groups,
                "description": manifest.description,
            }

        # Also add by service name if it has web access
        if manifest.name not in rules["services"] and manifest.has_web_access():
            rules["services"][manifest.name] = {
                "groups": manifest.access_groups,
                "description": manifest.description,
            }

    # Sort services alphabetically
    rules["services"] = dict(sorted(rules["services"].items()))

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate YAML with header comment
        header = """# Tailscale Access Rules
#
# This file defines:
# 1. Group memberships (must match Tailscale ACL policy)
# 2. Per-service access rules
#
# Used by the tailscale-access ForwardAuth middleware.
#
# AUTO-GENERATED FROM service.yml MANIFESTS - Edit manifests, not this file.

"""
        with open(output_path, "w") as f:
            f.write(header)
            yaml.dump(rules, f, default_flow_style=False, sort_keys=False)

    return rules


def sync_access_rules(services: Optional[list[str]] = None) -> Path:
    """Sync access rules file with current service manifests.

    Args:
        services: List of services to include. If None, uses all.

    Returns:
        Path to the generated access rules file.
    """
    output_path = TAILSCALE_PATH / "access-rules.yml"
    generate_access_rules(services=services, output_path=output_path)
    return output_path
