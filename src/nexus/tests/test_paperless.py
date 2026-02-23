from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

PAPERLESS_SERVICE_PATH = SERVICES_PATH / "paperless"
PAPERLESS_COMPOSE_PATH = PAPERLESS_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(PAPERLESS_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestPaperlessDockerCompose:
    def test_postgres_mount_path(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["paperless-db"]["volumes"]
        assert any("/var/lib/postgresql" in v for v in volumes)

    def test_web_depends_on_db_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["paperless-web"]["depends_on"]
        assert "paperless-db" in depends_on
        assert depends_on["paperless-db"]["condition"] == "service_healthy"

    def test_web_depends_on_redis_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["paperless-web"]["depends_on"]
        assert "paperless-redis" in depends_on
        assert depends_on["paperless-redis"]["condition"] == "service_healthy"

    def test_volume_paths_use_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["paperless-web"]["volumes"]
        assert any("/Config/paperless/" in v for v in volumes)

    def test_private_bridge_network_defined(
        self, compose_config: dict[str, Any]
    ) -> None:
        networks = compose_config["networks"]
        assert "paperless" in networks
        assert networks["paperless"].get("driver") == "bridge"

    def test_backend_containers_on_private_network_only(
        self, compose_config: dict[str, Any]
    ) -> None:
        for container_name in ("paperless-db", "paperless-redis"):
            networks = compose_config["services"][container_name]["networks"]
            assert "paperless" in networks
            assert "nexus" not in networks, (
                f"{container_name}: should not be on the nexus network"
            )
