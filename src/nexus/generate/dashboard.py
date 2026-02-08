import logging
from functools import cache
from typing import Any, Optional

import yaml

from nexus.config import SERVICES_PATH
from nexus.services import discover_services
from nexus.types import ServiceMetadata, TraefikConfig


@cache
def _get_service_metadata() -> dict[str, ServiceMetadata]:
    """Build metadata lookup from service manifests.

    Returns a flattened dict mapping service/sub-service names to their metadata
    (description, icon, category, dashboard_exclude, widget).

    Returns:
        Dict mapping service names to metadata dict with keys:
        'description', 'icon', 'category', 'dashboard_exclude', 'widget'.
    """
    metadata: dict[str, ServiceMetadata] = {}
    manifests = discover_services()

    for manifest in manifests.values():
        # Handle sub-services (e.g., monitoring -> grafana, prometheus)
        if manifest.sub_services:
            for sub_name, sub_config in manifest.sub_services.items():
                metadata[sub_name] = {
                    "description": sub_config.get("description", manifest.description),
                    "icon": sub_config.get("icon", manifest.icon),
                    "category": manifest.category,
                    "dashboard_exclude": sub_config.get("exclude", False),
                    "widget": sub_config.get("widget", {}),
                }
        else:
            # Single service
            metadata[manifest.name] = {
                "description": manifest.description,
                "icon": manifest.icon,
                "category": manifest.category,
                "dashboard_exclude": manifest.dashboard_exclude,
                "widget": manifest.widget,
            }

    return metadata


def get_service_config(service_name: str) -> list[TraefikConfig]:
    """Parse a service's docker-compose.yml to extract Traefik routing info.

    Reads the compose file and looks for Traefik labels to determine
    the service's hostname and routing rules. Returns a list of configs
    because one compose file might define multiple accessible services
    (e.g., monitoring stack has prometheus, grafana, etc.).

    Args:
        service_name: Name of the service directory to read from.

    Returns:
        List of dictionaries with keys 'name', 'container', 'rule', 'description',
        and 'icon' if Traefik labels are found.
    """
    compose_file = SERVICES_PATH / service_name / "docker-compose.yml"
    if not compose_file.exists():
        logging.warning(f"No docker-compose.yml found for {service_name}")
        return []

    with compose_file.open() as f:
        compose_data = yaml.safe_load(f)

    configs: list[TraefikConfig] = []
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
                # Use the container name (svc_name) as the key for lookup
                # This allows 'grafana', 'prometheus' to have distinct icons/desc
                # even if they are in 'monitoring' folder.
                configs.append(
                    {
                        "name": svc_name,
                        "container": svc_name,
                        "rule": rule,
                        "description": get_service_description(svc_name),
                        "icon": get_service_icon(svc_name),
                    }
                )

    return configs


def get_service_description(service_name: str) -> str:
    """Look up the human-readable description for a service.

    Args:
        service_name: Name of the service to look up.

    Returns:
        Description string for the service, or empty string if not found.
    """
    metadata = _get_service_metadata()
    # Safe because TypedDict guarantees 'description' is str if present,
    # or we handle missing key with default
    meta = metadata.get(service_name)
    return meta["description"] if meta else ""


def get_service_icon(service_name: str) -> str:
    """Look up the icon for a service.

    Args:
        service_name: Name of the service to look up.

    Returns:
        Icon identifier, or 'mdi-application' if not found.
    """
    metadata = _get_service_metadata()
    meta = metadata.get(service_name)
    return meta["icon"] if meta else "mdi-application"


def categorize_service(service_name: str) -> str:
    """Determine which dashboard category a service belongs to.

    Args:
        service_name: Name of the service to categorize.

    Returns:
        Category name (e.g., 'core', 'media'), or 'other' if not found.
    """
    metadata = _get_service_metadata()
    meta = metadata.get(service_name)
    category = meta["category"] if meta else "other"
    # Title-case for display
    return category.title()


def is_service_excluded(service_name: str) -> bool:
    """Check if a service should be excluded from the dashboard.

    Args:
        service_name: Name of the service to check.

    Returns:
        True if service should be excluded, False otherwise.
    """
    metadata = _get_service_metadata()
    meta = metadata.get(service_name)
    return meta["dashboard_exclude"] if meta else False


def get_service_widget(service_name: str) -> dict[str, Any]:
    """Get the widget configuration for a service.

    Args:
        service_name: Name of the service.

    Returns:
        Widget configuration dict, or empty dict if none defined.
    """
    metadata = _get_service_metadata()
    meta = metadata.get(service_name)
    return meta["widget"] if meta else {}


def generate_dashboard_config(
    services: list[str],
    domain: str,
    dry_run: bool = False,
    latitude: float = 49.2827,
    longitude: float = -123.1207,
    timezone: str = "America/Vancouver",
    units: str = "metric",
    city: str = "Vancouver",
    secrets: Optional[dict[str, Any]] = None,
) -> list[dict[str, list[dict[str, Any]]]]:
    """Generate Homepage dashboard configuration for the specified services.

    Reads each service's docker-compose.yml to extract Traefik routing rules
    and builds a Homepage-compatible configuration grouped by category.

    Args:
        services: List of service names to include in the dashboard.
            The "dashboard" service itself is automatically excluded.
        domain: Base domain used as fallback if Host rule not found.
        dry_run: If True, log what would be generated without side effects.
        latitude: Location latitude for weather widget.
        longitude: Location longitude for weather widget.
        timezone: Timezone identifier for weather data.
        units: Temperature units - "metric" or "imperial".
        city: City name for display.
        secrets: Dictionary of secrets for service widget authentication.

    Returns:
        List of dictionaries mapping category names to lists of service configurations,
        formatted for Homepage's services.yaml file.
        Each service configuration is a dict with structure:
        {service_name: {"href": str, "description": str, "icon": str, "widget": dict}}.
    """
    dashboard_config: dict[str, list[dict[str, Any]]] = {}
    secrets = secrets or {}

    for service_dir in services:
        if service_dir == "dashboard":
            continue

        service_configs = get_service_config(service_dir)
        for service_info in service_configs:
            svc_name = service_info["name"]

            if is_service_excluded(svc_name):
                continue

            rule = service_info.get("rule", "")

            if "Host(`" in rule:
                hostname = rule.split("Host(`")[1].split("`)")[0]
                # Replace placeholder with actual domain for absolute URLs
                if "${NEXUS_DOMAIN}" in hostname:
                    hostname = hostname.replace("${NEXUS_DOMAIN}", domain)
                url = f"https://{hostname}"
            else:
                url = f"https://{svc_name}.{domain}"

            category = categorize_service(svc_name)

            if category not in dashboard_config:
                dashboard_config[category] = []

            dashboard_config[category].append(
                {
                    svc_name: {
                        "href": url,
                        "description": service_info["description"],
                        "icon": service_info["icon"],
                    }
                }
            )

            # Inject widget config from manifest
            widget_config = get_service_widget(svc_name)

            # Inject secrets into widget config if needed
            if widget_config:
                widget_config = dict(widget_config)  # Copy to avoid mutating cached
                widget_type = widget_config.get("type", "")

                # Handle secret substitutions
                if widget_type == "grafana":
                    widget_config.setdefault(
                        "username", secrets.get("grafana_admin_user", "admin")
                    )
                    if secrets.get("grafana_admin_password"):
                        widget_config["password"] = secrets["grafana_admin_password"]
                    else:
                        widget_config = {}  # Skip if no password
                elif widget_type == "jellyfin":
                    if secrets.get("jellyfin_api_key"):
                        widget_config["key"] = secrets["jellyfin_api_key"]
                    else:
                        widget_config = {}  # Skip if no API key
                elif widget_type == "plex":
                    if secrets.get("plex_token"):
                        widget_config["key"] = secrets["plex_token"]
                    else:
                        widget_config = {}  # Skip if no token

            if widget_config:
                dashboard_config[category][-1][svc_name]["widget"] = widget_config

    # Sort services within each category before returning
    for category in dashboard_config:
        dashboard_config[category].sort(key=lambda x: next(iter(x.keys())).lower())

    final_config = []
    for category in sorted(dashboard_config.keys()):
        final_config.append({category: dashboard_config[category]})

    if dry_run:
        logging.info("[DRY RUN] Would write dashboard config:")
        logging.info(f"[DRY RUN] Services: {services}")
        logging.info(f"[DRY RUN] Domain: {domain}")
        return final_config

    return final_config


def generate_settings_config() -> dict[str, Any]:
    """Generate the settings.yaml configuration.

    Uses system theme auto-detection (no explicit theme set) so the dashboard
    automatically matches the user's OS dark/light mode preference.

    Returns:
        Dictionary containing the settings configuration.
    """
    return {
        "title": "Nexus",
        "background": {
            "image": "/images/background.png",
            "opacity": 30,
        },
        "color": "slate",
        "cardBlur": "md",
        "headerStyle": "clean",
        "statusStyle": "dot",
        "hideVersion": True,
        "layout": {
            "Media": {"style": "row", "columns": 2},
            "Finance": {"style": "row", "columns": 2},
            "Gaming": {"style": "row", "columns": 2},
            "Core": {"style": "row", "columns": 2},
            "Utilities": {"style": "row", "columns": 2},
        },
    }


def generate_bookmarks_config() -> list[dict[str, Any]]:
    """Generate the bookmarks.yaml configuration.

    Returns:
        List of bookmark categories and items.
    """
    return [
        {
            "Productivity": [
                {"Github": [{"icon": "si-github", "href": "https://github.com/"}]},
                {"Gmail": [{"icon": "si-gmail", "href": "https://mail.google.com/"}]},
                {
                    "ProtonMail": [
                        {"icon": "si-protonmail", "href": "https://mail.proton.me/"}
                    ]
                },
                {
                    "Cloudflare": [
                        {
                            "icon": "si-cloudflare",
                            "href": "https://dash.cloudflare.com/",
                        }
                    ]
                },
                {
                    "Tailscale": [
                        {
                            "icon": "si-tailscale",
                            "href": "https://login.tailscale.com/admin/machines",
                        }
                    ]
                },
                {
                    "SimpleFIN": [
                        {
                            "icon": "mdi-bank",
                            "href": "https://beta-bridge.simplefin.org/",
                        }
                    ]
                },
            ]
        },
    ]


def generate_widgets_config(
    latitude: float = 49.2827,
    longitude: float = -123.1207,
    timezone: str = "America/Vancouver",
    units: str = "metric",
) -> list[dict[str, Any]]:
    """Generate the widgets.yaml configuration with weather and info widgets.

    Args:
        latitude: Location latitude for weather (default: Vancouver).
        longitude: Location longitude for weather (default: Vancouver).
        timezone: Timezone identifier for weather data.
        units: Temperature units - "metric" or "imperial".

    Returns:
        List of widget configurations for Homepage.
    """
    return [
        {
            "resources": {
                "cpu": True,
                "memory": True,
                "disk": "/",
            }
        },
        {
            "datetime": {
                "text_size": "lg",
                "format": {
                    "dateStyle": "long",
                    "timeStyle": "short",
                    "hour12": True,
                },
            }
        },
        {
            "openmeteo": {
                "label": "Weather",
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "units": units,
                "cache": 5,
            }
        },
    ]
