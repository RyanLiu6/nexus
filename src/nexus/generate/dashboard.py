import logging
from typing import Any

import yaml

from nexus.config import SERVICES_PATH

DESCRIPTIONS = {
    "traefik": "Reverse proxy and SSL management",
    "dashboard": "Homepage dashboard",
    "plex": "Media streaming",
    "jellyfin": "Media server",
    "transmission": "Torrent client",
    "sure-web": "Finance and budgeting",
    "foundryvtt": "Virtual Tabletop",
    "nextcloud": "File storage",
    "prometheus": "Metrics database",
    "grafana": "Metrics dashboards",
    "alertmanager": "Alert management",
}

ICONS = {
    "traefik": "si-traefikproxy",
    "dashboard": "si-homeassistant",
    "plex": "si-plex",
    "jellyfin": "si-jellyfin",
    "transmission": "si-transmission",
    "sure-web": "mdi-finance",
    "foundryvtt": "si-foundryvirtualtabletop",
    "nextcloud": "si-nextcloud",
    "prometheus": "si-prometheus",
    "grafana": "si-grafana",
    "alertmanager": "si-prometheus",
}

CATEGORIES = {
    "traefik": "Core",
    "dashboard": "Core",
    "plex": "Media",
    "jellyfin": "Media",
    "transmission": "Media",
    "sure-web": "Finance",
    "foundryvtt": "Gaming",
    "nextcloud": "Files",
    "prometheus": "Core",
    "grafana": "Core",
    "alertmanager": "Core",
}

EXCLUDED_SERVICES = [
    "node-exporter",
    "tailscale-access",
    "alert-bot",
    "sure-db",
    "sure-redis",
    "sure-worker",
]


def get_service_config(service_name: str) -> list[dict[str, Any]]:
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

    configs: list[dict[str, Any]] = []
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
    services: list[str],
    domain: str,
    dry_run: bool = False,
    latitude: float = 49.2827,
    longitude: float = -123.1207,
    timezone: str = "America/Vancouver",
    units: str = "metric",
    city: str = "Vancouver",
    secrets: dict[str, Any] | None = None,
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
    """
    dashboard_config: dict[str, list[dict[str, Any]]] = {}
    secrets = secrets or {}

    for service_dir in services:
        if service_dir == "dashboard":
            continue

        service_configs = get_service_config(service_dir)
        for service_info in service_configs:
            svc_name = service_info["name"]

            if svc_name in EXCLUDED_SERVICES:
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

            # Inject Service Widget if supported
            widget_config = {}
            if svc_name == "traefik":
                widget_config = {"type": "traefik", "url": "http://traefik:8080"}
            elif svc_name == "grafana":
                user = secrets.get("grafana_admin_user", "admin")
                pw = secrets.get("grafana_admin_password")
                if pw:
                    widget_config = {
                        "type": "grafana",
                        "url": "http://grafana:3000",
                        "username": user,
                        "password": pw,
                    }
            elif svc_name == "prometheus":
                widget_config = {"type": "prometheus", "url": "http://prometheus:9090"}
            elif svc_name == "transmission":
                # Transmission might need auth if configured, but default often internal
                widget_config = {
                    "type": "transmission",
                    "url": "http://transmission:9091",
                }
            elif svc_name == "jellyfin":
                key = secrets.get("jellyfin_api_key")
                if key:
                    widget_config = {
                        "type": "jellyfin",
                        "url": "http://jellyfin:8096",
                        "key": key,
                    }
            elif svc_name == "plex":
                token = secrets.get("plex_token")
                if token:
                    widget_config = {
                        "type": "plex",
                        "url": "http://plex:32400",
                        "key": token,
                    }

            if widget_config:
                dashboard_config[category][-1][svc_name]["widget"] = widget_config

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
