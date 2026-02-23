from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

BOOKLORE_SERVICE_PATH = SERVICES_PATH / "booklore"
BOOKLORE_COMPOSE_PATH = BOOKLORE_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(BOOKLORE_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestBookloreDockerCompose:
    def test_db_uses_mariadb_image(self, compose_config: dict[str, Any]) -> None:
        image = compose_config["services"]["booklore-db"]["image"]
        assert "mariadb" in image.lower()

    def test_volume_paths_use_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["booklore"]["volumes"]
        assert any("/Config/booklore/" in v for v in volumes)

    def test_db_volume_uses_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["booklore-db"]["volumes"]
        assert any("/Config/booklore/" in v for v in volumes)

    def test_web_depends_on_db_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["booklore"]["depends_on"]
        assert "booklore-db" in depends_on
        assert depends_on["booklore-db"]["condition"] == "service_healthy"

    def test_private_bridge_network_defined(
        self, compose_config: dict[str, Any]
    ) -> None:
        networks = compose_config["networks"]
        assert "booklore" in networks
        assert networks["booklore"].get("driver") == "bridge"

    def test_db_on_private_network_only(self, compose_config: dict[str, Any]) -> None:
        db_networks = compose_config["services"]["booklore-db"]["networks"]
        assert "booklore" in db_networks
        assert "nexus" not in db_networks
