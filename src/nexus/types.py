from typing import Any, TypedDict


class ServiceMetadata(TypedDict):
    """Metadata dictionary for a service or sub-service.

    Attributes:
        description: Human-readable description of the service.
        icon: Icon identifier (e.g., "si-plex", "mdi-application").
        category: Service category for dashboard grouping (e.g., "core", "home").
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
    """Cloudflare R2 storage credentials for FoundryVTT S3-compatible storage.

    Retrieved from Terraform outputs during deployment and passed to Ansible
    as extra-vars for configuring Foundry's S3 storage backend.

    Attributes:
        endpoint: R2 endpoint URL for the storage bucket.
        access_key: R2 access key ID for authentication.
        secret_key: R2 secret access key for authentication.
        bucket: Name of the R2 storage bucket.
    """

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


class TraefikConfig(TypedDict):
    """Traefik routing metadata for a single container from docker-compose labels.

    Built by parsing Traefik labels from a service's docker-compose.yml and consumed
    by the dashboard generator to create Homepage service entries with correct URLs.

    Attributes:
        name: Service name derived from the Traefik router name.
        container: Docker container name running the service.
        rule: Traefik routing rule (e.g., "Host(`grafana.${NEXUS_DOMAIN}`)").
        description: Human-readable service description from the service manifest.
        icon: Icon identifier for dashboard display (e.g., "si-grafana").
    """

    name: str
    container: str
    rule: str
    description: str
    icon: str
