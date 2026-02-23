from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

ALL_SERVICES = [
    "backups",
    "booklore",
    "cloudflared",
    "dashboard",
    "foundryvtt",
    "jellyfin",
    "monitoring",
    "nextcloud",
    "paperless",
    "plex",
    "sure",
    "tailscale-access",
    "traefik",
    "transmission",
    "vaultwarden",
]

# Services where the standard HTTPS + tailscale-chain Traefik pattern doesn't apply
_TRAEFIK_HTTPS_SKIP = {
    "cloudflared",
    "backups",
    "tailscale-access",
    "foundryvtt",
    "traefik",
}
_TRAEFIK_HTTPS_SERVICES = [s for s in ALL_SERVICES if s not in _TRAEFIK_HTTPS_SKIP]

# (service, container) pairs with DB/redis containers that must have healthchecks
_DB_REDIS_CONTAINERS = [
    ("booklore", "booklore-db"),
    ("paperless", "paperless-db"),
    ("paperless", "paperless-redis"),
    ("sure", "sure-db"),
    ("sure", "sure-redis"),
]


def _load_compose(service_name: str) -> dict[str, Any]:
    compose_path = SERVICES_PATH / service_name / "docker-compose.yml"
    with open(compose_path) as f:
        return dict(yaml.safe_load(f))


@pytest.mark.parametrize("service_name", ALL_SERVICES)
def test_compose_file_exists(service_name: str) -> None:
    assert (SERVICES_PATH / service_name / "docker-compose.yml").exists()


@pytest.mark.parametrize("service_name", ALL_SERVICES)
def test_service_manifest_exists(service_name: str) -> None:
    assert (SERVICES_PATH / service_name / "service.yml").exists()


@pytest.mark.parametrize("service_name", ALL_SERVICES)
def test_all_containers_have_memory_limits(service_name: str) -> None:
    config = _load_compose(service_name)
    for container_name, container_config in config["services"].items():
        deploy = container_config.get("deploy", {})
        assert "resources" in deploy, f"{container_name}: missing deploy.resources"
        assert "limits" in deploy["resources"], (
            f"{container_name}: missing deploy.resources.limits"
        )
        assert "memory" in deploy["resources"]["limits"], (
            f"{container_name}: missing memory limit"
        )


@pytest.mark.parametrize("service_name", ALL_SERVICES)
def test_all_containers_have_restart_policy(service_name: str) -> None:
    config = _load_compose(service_name)
    for container_name, container_config in config["services"].items():
        assert container_config.get("restart") == "unless-stopped", (
            f"{container_name}: expected restart: unless-stopped"
        )


@pytest.mark.parametrize("service_name", _TRAEFIK_HTTPS_SERVICES)
def test_web_containers_have_traefik_https_labels(service_name: str) -> None:
    config = _load_compose(service_name)
    containers_with_https = 0

    for container_name, container_config in config["services"].items():
        labels = container_config.get("labels", [])
        if not labels:
            continue

        has_https = any("entrypoints=https" in label for label in labels)
        if not has_https:
            continue

        containers_with_https += 1
        has_tailscale = any("tailscale-chain@file" in label for label in labels)
        assert has_tailscale, (
            f"{container_name}: has entrypoints=https but missing "
            "tailscale-chain@file middleware"
        )

    assert containers_with_https > 0, (
        f"{service_name}: no containers with HTTPS entrypoints found"
    )


@pytest.mark.parametrize("service_name,container_name", _DB_REDIS_CONTAINERS)
def test_db_containers_have_healthchecks(
    service_name: str, container_name: str
) -> None:
    config = _load_compose(service_name)
    container = config["services"][container_name]
    healthcheck = container.get("healthcheck")
    assert healthcheck is not None, f"{container_name}: missing healthcheck"
    assert "test" in healthcheck, f"{container_name}: healthcheck missing test command"
    assert "interval" in healthcheck, f"{container_name}: healthcheck missing interval"
