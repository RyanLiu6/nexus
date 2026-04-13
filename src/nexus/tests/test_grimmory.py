from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

GRIMMORY_SERVICE_PATH = SERVICES_PATH / "grimmory"
GRIMMORY_COMPOSE_PATH = GRIMMORY_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(GRIMMORY_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestGrimmoryDockerCompose:
    def test_db_uses_mariadb_image(self, compose_config: dict[str, Any]) -> None:
        image = compose_config["services"]["grimmory-db"]["image"]
        assert "mariadb" in image.lower()

    def test_volume_paths_use_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["grimmory"]["volumes"]
        assert any("GRIMMORY_BOOKS_DIRECTORY" in v for v in volumes)
        assert any("/Config/grimmory/" in v for v in volumes)

    def test_db_volume_uses_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["grimmory-db"]["volumes"]
        assert any("/Config/grimmory/" in v for v in volumes)

    def test_web_depends_on_db_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["grimmory"]["depends_on"]
        assert "grimmory-db" in depends_on
        assert depends_on["grimmory-db"]["condition"] == "service_healthy"

    def test_private_bridge_network_defined(
        self, compose_config: dict[str, Any]
    ) -> None:
        networks = compose_config["networks"]
        assert "grimmory" in networks
        assert networks["grimmory"].get("driver") == "bridge"

    def test_db_on_private_network_only(self, compose_config: dict[str, Any]) -> None:
        db_networks = compose_config["services"]["grimmory-db"]["networks"]
        assert "grimmory" in db_networks
        assert "nexus" not in db_networks
