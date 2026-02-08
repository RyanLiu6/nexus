from typing import Any, TypedDict


class ServiceMetadata(TypedDict):
    """Metadata dictionary for a service or sub-service.

    Attributes:
        description: Human-readable description of the service.
        icon: Icon identifier (e.g., "si-plex", "mdi-application").
        category: Service category for dashboard grouping (e.g., "core", "home).
        dashboard_exclude: Whether to exclude this service from the dashboard.
        widget: Homepage widget configuration dictionary.
            Structure: {"type": str, "url": str}, with optional runtime keys
            "username", "password", or "key" injected from vault secrets.
    """

    description: str
    icon: str
    category: str
    dashboard_exclude: bool
    widget: dict[str, Any]


class R2Credentials(TypedDict):
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


class TraefikConfig(TypedDict):
    name: str
    container: str
    rule: str
    description: str
    icon: str
