import logging
from typing import Any

import yaml

from nexus.config import SERVICES_PATH

DESCRIPTIONS = {
    "traefik": "Reverse proxy and SSL management",
    "dashboard": "Homepage dashboard",
    "backups": "Automated backups",
    "plex": "Media streaming",
    "jellyfin": "Media server",
    "transmission": "Torrent client",
    "sure": "Finance and budgeting",
    "foundryvtt": "Virtual Tabletop",
    "nextcloud": "File storage",
    "monitoring": "Metrics collection and visualization",
    "tailscale-access": "Auth Middleware",
}

ICONS = {
    "traefik": "traefik.png",
    "dashboard": "homepage.png",
    "backups": "borg.png",
    "plex": "plex.png",
    "jellyfin": "jellyfin.png",
    "transmission": "transmission.png",
    "sure": "sh-sure.png",
    "foundryvtt": "foundryvtt.png",
    "nextcloud": "nextcloud.png",
    "monitoring": "prometheus.png",
    "tailscale-access": "tailscale.png",
}

CATEGORIES = {
    "traefik": "Core",
    "dashboard": "Core",
    "backups": "Utilities",
    "plex": "Media",
    "jellyfin": "Media",
    "transmission": "Media",
    "sure": "Finance",
    "foundryvtt": "Gaming",
    "nextcloud": "Files",
    "monitoring": "Core",
    "tailscale-access": "Core",
}


def get_service_config(service_name: str) -> dict[str, Any]:
    """Parse a service's docker-compose.yml to extract Traefik routing info.

    Reads the compose file and looks for Traefik labels to determine
    the service's hostname and routing rules.

    Args:
        service_name: Name of the service directory to read from.

    Returns:
        Dictionary with keys 'name', 'container', 'rule', 'description',
        and 'icon' if Traefik labels are found. Empty dict if the compose
        file doesn't exist or has no Traefik configuration.
    """
    compose_file = SERVICES_PATH / service_name / "docker-compose.yml"
    if not compose_file.exists():
        logging.warning(f"No docker-compose.yml found for {service_name}")
        return {}

    with compose_file.open() as f:
        compose_data = yaml.safe_load(f)

    service_info: dict[str, Any] = {}
    services = compose_data.get("services", {})

    for svc_name, svc_config in services.items():
        labels = svc_config.get("labels", [])
        if isinstance(labels, list):
            labels_dict = {
                label.split("=")[0]: "=".join(label.split("=")[1:])
                for label in labels
                if "=" in label
            }
        else:
            labels_dict = labels or {}

        if "traefik.http.routers" in str(labels_dict):
            router_label = [
                k
                for k in labels_dict.keys()
                if "traefik.http.routers" in k and ".rule" in k
            ]
            if router_label:
                rule = labels_dict[router_label[0]]
                service_info = {
                    "name": service_name,
                    "container": svc_name,
                    "rule": rule,
                    "description": get_service_description(service_name),
                    "icon": get_service_icon(service_name),
                }
                break

    return service_info


def get_service_description(service_name: str) -> str:
    """Look up the human-readable description for a service.

    Args:
        service_name: Name of the service to look up.

    Returns:
        Description string for the service, or empty string if not found.
    """
    return DESCRIPTIONS.get(service_name, "")


def get_service_icon(service_name: str) -> str:
    """Look up the icon filename for a service.

    Args:
        service_name: Name of the service to look up.

    Returns:
        Icon filename (e.g., "traefik.png"), or "unknown.png" if not found.
    """
    return ICONS.get(service_name, "unknown.png")


def categorize_service(service_name: str) -> str:
    """Determine which dashboard category a service belongs to.

    Args:
        service_name: Name of the service to categorize.

    Returns:
        Category name (e.g., "Core", "Media"), or "Other" if not found.
    """
    return CATEGORIES.get(service_name, "Other")


def generate_dashboard_config(
    services: list[str], domain: str, dry_run: bool = False
) -> list[dict[str, list[dict[str, Any]]]]:
    """Generate Homepage dashboard configuration for the specified services.

    Reads each service's docker-compose.yml to extract Traefik routing rules
    and builds a Homepage-compatible configuration grouped by category.

    Args:
        services: List of service names to include in the dashboard.
            The "dashboard" service itself is automatically excluded.
        domain: Base domain used as fallback if Host rule not found.
        dry_run: If True, log what would be generated without side effects.

    Returns:
        List of dictionaries mapping category names to lists of service configurations,
        formatted for Homepage's services.yaml file.
    """
    dashboard_config: dict[str, list[dict[str, Any]]] = {}

    for service_name in services:
        if service_name == "dashboard":
            continue

        service_info = get_service_config(service_name)
        if not service_info:
            continue

        rule = service_info.get("rule", "")
        if "Host(`" in rule:
            hostname = rule.split("Host(`")[1].split("`)")[0]
            url = f"https://{hostname}"
        else:
            url = f"https://{service_name}.{domain}"

        category = categorize_service(service_name)

        if category not in dashboard_config:
            dashboard_config[category] = []

        dashboard_config[category].append(
            {
                service_name: {
                    "href": url,
                    "description": service_info["description"],
                    "icon": service_info["icon"],
                }
            }
        )

    # Convert to list format expected by Homepage
    final_config = []
    for category, items in dashboard_config.items():
        final_config.append({category: items})

    if dry_run:
        logging.info("[DRY RUN] Would write dashboard config:")
        logging.info(f"[DRY RUN] Services: {services}")
        logging.info(f"[DRY RUN] Domain: {domain}")
        return final_config

    return final_config
