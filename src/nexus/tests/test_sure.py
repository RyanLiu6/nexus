from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

SURE_SERVICE_PATH = SERVICES_PATH / "sure"
SURE_COMPOSE_PATH = SURE_SERVICE_PATH / "docker-compose.yml"

_EXPECTED_CONTAINERS = {"sure-web", "sure-worker", "sure-db", "sure-redis"}


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(SURE_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestSureDockerCompose:
    def test_all_four_containers_exist(self, compose_config: dict[str, Any]) -> None:
        assert set(compose_config["services"].keys()) == _EXPECTED_CONTAINERS

    def test_worker_container_exists(self, compose_config: dict[str, Any]) -> None:
        assert "sure-worker" in compose_config["services"]

    def test_db_has_shm_size(self, compose_config: dict[str, Any]) -> None:
        assert "shm_size" in compose_config["services"]["sure-db"]

    def test_web_depends_on_db_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["sure-web"]["depends_on"]
        assert depends_on["sure-db"]["condition"] == "service_healthy"

    def test_web_depends_on_redis_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["sure-web"]["depends_on"]
        assert depends_on["sure-redis"]["condition"] == "service_healthy"

    def test_worker_depends_on_db_healthy(self, compose_config: dict[str, Any]) -> None:
        depends_on = compose_config["services"]["sure-worker"]["depends_on"]
        assert depends_on["sure-db"]["condition"] == "service_healthy"

    def test_worker_depends_on_redis_healthy(
        self, compose_config: dict[str, Any]
    ) -> None:
        depends_on = compose_config["services"]["sure-worker"]["depends_on"]
        assert depends_on["sure-redis"]["condition"] == "service_healthy"

    def test_private_bridge_network_defined(
        self, compose_config: dict[str, Any]
    ) -> None:
        networks = compose_config["networks"]
        assert "sure" in networks
        assert networks["sure"].get("driver") == "bridge"

    def test_backend_containers_on_private_network_only(
        self, compose_config: dict[str, Any]
    ) -> None:
        for container_name in ("sure-db", "sure-redis", "sure-worker"):
            networks = compose_config["services"][container_name]["networks"]
            assert "sure" in networks
            assert "nexus" not in networks, (
                f"{container_name}: should not be on the nexus network"
            )
