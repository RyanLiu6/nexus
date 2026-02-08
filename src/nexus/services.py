from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from nexus.config import SERVICES_PATH


@dataclass
class ServiceManifest:
    """Service manifest parsed from service.yml files.

    Attributes:
        name: Service identifier.
        description: Human-readable description.
        category: Dashboard category (e.g., 'Core', 'Media').
        subdomains: List of subdomains routing to this service.
        access_groups: List of groups allowed access.
        is_public: Whether service is publicly accessible.
        dependencies: List of service names this service depends on.
        path: Path to the service directory.
        icon: Dashboard icon identifier (e.g., 'si-plex').
        display_name: Optional human-readable display name.
        dashboard_exclude: Whether to exclude from the dashboard.
        widget: Homepage widget configuration dict (e.g., {'type': 'grafana', ...}).
        sub_services: Dictionary of sub-services for composite
            stacks (e.g., monitoring).
            Structure:
            {'sub_name': {'icon': str, 'description': str, 'widget': dict}}
    """

    name: str
    description: str
    category: str
    subdomains: list[str] = field(default_factory=list)
    access_groups: list[str] = field(default_factory=list)
    is_public: bool = False
    dependencies: list[str] = field(default_factory=list)
    path: Path = field(default_factory=Path)
    # Dashboard configuration
    icon: str = "mdi-application"
    display_name: str = ""
    dashboard_exclude: bool = False
    widget: dict[str, Any] = field(default_factory=dict)
    sub_services: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "ServiceManifest":
        """Load a service manifest from a YAML file.

        Args:
            path: Path to the service.yml file.

        Returns:
            Parsed ServiceManifest.

        Raises:
            FileNotFoundError: If the manifest doesn't exist.
            ValueError: If required fields are missing.
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        # Handle subdomain/subdomains flexibility
        subdomains = []
        if "subdomains" in data:
            subdomains = data["subdomains"]
        elif data.get("subdomain"):
            subdomains = [data["subdomain"]]

        # Parse access config
        access = data.get("access", {})
        access_groups = access.get("groups", [])
        is_public = access.get("public", False)

        # Parse dashboard config
        dashboard = data.get("dashboard", {})
        dashboard_exclude = dashboard.get("exclude", False)
        widget = dashboard.get("widget", {})

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "other"),
            subdomains=subdomains,
            access_groups=access_groups,
            is_public=is_public,
            dependencies=data.get("dependencies", []),
            path=path.parent,
            icon=data.get("icon", "mdi-application"),
            display_name=data.get("display_name", ""),
            dashboard_exclude=dashboard_exclude,
            widget=widget,
            sub_services=data.get("services", {}),
        )

    def has_web_access(self) -> bool:
        """Check if service has web access configuration.

        Returns:
            True if the service has subdomains or is public, False otherwise.
        """
        return bool(self.subdomains) or self.is_public


def discover_services(
    services_path: Optional[Path] = None,
) -> dict[str, ServiceManifest]:
    """Discover all services with manifest files.

    Args:
        services_path: Path to services directory. Defaults to SERVICES_PATH.

    Returns:
        Dictionary mapping service name to its manifest.
    """
    if services_path is None:
        services_path = SERVICES_PATH

    services = {}
    for service_dir in services_path.iterdir():
        if not service_dir.is_dir():
            continue

        manifest_path = service_dir / "service.yml"
        if manifest_path.exists():
            try:
                manifest = ServiceManifest.from_yaml(manifest_path)
                services[manifest.name] = manifest
            except (yaml.YAMLError, KeyError, ValueError):
                # Skip invalid manifests
                continue

    return services


def get_all_service_names(services_path: Optional[Path] = None) -> list[str]:
    """Get sorted list of all discovered service names.

    Args:
        services_path: Path to services directory. Defaults to SERVICES_PATH.

    Returns:
        Sorted list of service names.
    """
    return sorted(discover_services(services_path).keys())


def get_services_by_category(
    services_path: Optional[Path] = None,
) -> dict[str, list[ServiceManifest]]:
    """Group services by category.

    Args:
        services_path: Path to services directory. Defaults to SERVICES_PATH.

    Returns:
        Dictionary mapping category to list of services.
    """
    services = discover_services(services_path)
    by_category: dict[str, list[ServiceManifest]] = {}

    for manifest in services.values():
        category = manifest.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(manifest)

    # Sort services within each category
    for category in by_category:
        by_category[category].sort(key=lambda m: m.name)

    return by_category


def get_public_services(services_path: Optional[Path] = None) -> list[ServiceManifest]:
    """Get all services that are publicly accessible.

    Args:
        services_path: Path to services directory. Defaults to SERVICES_PATH.

    Returns:
        List of public service manifests.
    """
    return [m for m in discover_services(services_path).values() if m.is_public]


def resolve_dependencies(
    service_names: list[str],
    all_services: dict[str, ServiceManifest],
) -> list[str]:
    """Resolve service dependencies to get full list of required services.

    Args:
        service_names: List of services to resolve.
        all_services: Dictionary of all available services.

    Returns:
        List of service names including all dependencies.
    """
    resolved = set()
    to_process = list(service_names)

    while to_process:
        name = to_process.pop(0)
        if name in resolved:
            continue

        resolved.add(name)

        if name in all_services:
            for dep in all_services[name].dependencies:
                if dep not in resolved:
                    to_process.append(dep)

    return sorted(resolved)
