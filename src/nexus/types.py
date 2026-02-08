"""Shared type definitions for Nexus."""

from typing import Any, TypedDict


class ServiceMetadata(TypedDict):
    """Metadata dictionary for a service or sub-service."""

    description: str
    icon: str
    category: str
    dashboard_exclude: bool
    widget: dict[str, Any]


class R2Credentials(TypedDict):
    """Credentials for Cloudflare R2 storage."""

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


class TraefikConfig(TypedDict):
    """Traefik configuration extracted from docker-compose labels."""

    name: str
    container: str
    rule: str
    description: str
    icon: str
