from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ServiceManifest:
    """Service manifest parsed from service.yml files.

    Attributes:
        name: Service identifier.
        description: Human-readable description.
        subdomains: List of subdomains routing to this service.
        is_public: Whether service is publicly accessible.
        dependencies: List of service names this service depends on.
        path: Path to the service directory.
    """

    name: str
    description: str
    subdomains: list[str] = field(default_factory=list)
    is_public: bool = False
    dependencies: list[str] = field(default_factory=list)
    path: Path = field(default_factory=Path)

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

        is_public = data.get("public", data.get("access", {}).get("public", False))

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            subdomains=subdomains,
            is_public=is_public,
            dependencies=data.get("dependencies", []),
            path=path.parent,
        )

    def has_web_access(self) -> bool:
        """Check if service has web access configuration.

        Returns:
            True if the service has subdomains.
        """
        return bool(self.subdomains)


def discover_services(
    services_path: Optional[Path] = None,
) -> dict[str, ServiceManifest]:
    """Discover all services with manifest files.

    Args:
        services_path: Path to services directory. Defaults to SERVICES_PATH
            and PRIVATE_SERVICES_PATH (if configured).

    Returns:
        Dictionary mapping service name to its manifest.
    """
    from nexus.config import PRIVATE_SERVICES_PATH, SERVICES_PATH

    if services_path is not None:
        paths_to_scan = [services_path]
    else:
        paths_to_scan = [SERVICES_PATH]
        if PRIVATE_SERVICES_PATH and PRIVATE_SERVICES_PATH.exists():
            paths_to_scan.append(PRIVATE_SERVICES_PATH)

    services = {}
    for base_path in paths_to_scan:
        if not base_path.is_dir():
            continue
        for service_dir in base_path.iterdir():
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
