from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

BOOKORBIT_SERVICE_PATH = SERVICES_PATH / "bookorbit"
BOOKORBIT_COMPOSE_PATH = BOOKORBIT_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(BOOKORBIT_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestBookorbitDockerCompose:
    def test_db_uses_pgvector_image(self, compose_config: dict[str, Any]) -> None:
        image = compose_config["services"]["bookorbit-db"]["image"]
        assert "pgvector" in image.lower()

    def test_volume_paths_use_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["bookorbit"]["volumes"]
        assert any("BOOKORBIT_BOOKS_DIRECTORY" in v for v in volumes)
        assert any("/Config/bookorbit/" in v for v in volumes)

    def test_db_volume_uses_config_dir(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["bookorbit-db"]["volumes"]
        assert any("/Config/bookorbit/" in v for v in volumes)

    def test_web_depends_on_db_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["bookorbit"]["depends_on"]
        assert "bookorbit-db" in depends_on
        assert depends_on["bookorbit-db"]["condition"] == "service_healthy"

    def test_private_bridge_network_defined(
        self, compose_config: dict[str, Any]
    ) -> None:
        networks = compose_config["networks"]
        assert "bookorbit" in networks
        assert networks["bookorbit"].get("driver") == "bridge"

    def test_db_on_private_network_only(self, compose_config: dict[str, Any]) -> None:
        db_networks = compose_config["services"]["bookorbit-db"]["networks"]
        assert "bookorbit" in db_networks
        assert "nexus" not in db_networks
