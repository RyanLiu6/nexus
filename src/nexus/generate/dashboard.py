import logging
from typing import Any

import yaml

from nexus.config import SERVICES_PATH


def get_service_config(service_name: str) -> dict[str, Any]:
    """Read docker-compose.yml for a service and extract relevant info.

    Args:
        service_name: The name of the service to retrieve configuration for.

    Returns:
        A dictionary containing the service configuration, or an empty dictionary
        if the configuration file is not found.
    """
    compose_file = SERVICES_PATH / service_name / "docker-compose.yml"
    if not compose_file.exists():
        logging.warning(f"No docker-compose.yml found for {service_name}")
        return {}

    with compose_file.open() as f:
        compose_data = yaml.safe_load(f)

    service_info = {}
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
    """Get description for a service.

    Args:
        service_name: The name of the service.

    Returns:
        The description of the service, or an empty string if not found.
    """
    descriptions = {
        "traefik": "Reverse proxy and SSL management",
        "auth": "SSO and 2FA authentication",
        "dashboard": "Homepage dashboard",
        "backups": "Automated backups",
        "plex": "Media streaming",
        "jellyfin": "Media server",
        "transmission": "Torrent client",
        "sure": "Finance and budgeting",
        "foundryvtt": "Virtual Tabletop",
        "nextcloud": "File storage",
        "monitoring": "Metrics collection and visualization",
    }
    return descriptions.get(service_name, "")


def get_service_icon(service_name: str) -> str:
    """Get icon filename for a service.

    Args:
        service_name: The name of the service.

    Returns:
        The filename of the service's icon.
    """
    icons = {
        "traefik": "traefik.png",
        "auth": "authelia.png",
        "dashboard": "homepage.png",
        "backups": "borg.png",
        "plex": "plex.png",
        "jellyfin": "jellyfin.png",
        "transmission": "transmission.png",
        "sure": "sh-sure.png",
        "foundryvtt": "foundryvtt.png",
        "nextcloud": "nextcloud.png",
        "monitoring": "prometheus.png",
    }
    return icons.get(service_name, "unknown.png")


def categorize_service(service_name: str) -> str:
    """Categorize service for dashboard.

    Args:
        service_name: The name of the service.

    Returns:
        The category of the service.
    """
    categories = {
        "traefik": "Core",
        "auth": "Core",
        "dashboard": "Core",
        "backups": "Utilities",
        "plex": "Media",
        "jellyfin": "Media",
        "transmission": "Media",
        "sure": "Finance",
        "foundryvtt": "Gaming",
        "nextcloud": "Files",
        "monitoring": "Core",
    }
    return categories.get(service_name, "Other")


def generate_dashboard_config(
    services: list[str], domain: str, dry_run: bool = False
) -> dict[str, Any]:
    """Generate Homepage dashboard config from selected services.

    Args:
        services: A list of service names to include in the dashboard.
        domain: The base domain for the services.
        dry_run: Whether to perform a dry run (log output instead of returning).

    Returns:
        A dictionary representing the dashboard configuration.
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

    if dry_run:
        logging.info("[DRY RUN] Would write dashboard config:")
        logging.info(f"[DRY RUN] Services: {services}")
        logging.info(f"[DRY RUN] Domain: {domain}")
        return dashboard_config

    return dashboard_config
