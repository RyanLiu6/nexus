from typing import Any

import pytest
import yaml

from nexus.services import discover_services

BESZEL_COMPOSE_PATH = discover_services()["beszel"].path / "docker-compose.yml"
UPTIME_KUMA_COMPOSE_PATH = (
    discover_services()["uptime-kuma"].path / "docker-compose.yml"
)


@pytest.fixture
def beszel_compose() -> dict[str, Any]:
    with open(BESZEL_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


@pytest.fixture
def uptime_kuma_compose() -> dict[str, Any]:
    with open(UPTIME_KUMA_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestBeszelDockerCompose:
    def test_hub_and_agent_present(self, beszel_compose: dict[str, Any]) -> None:
        assert set(beszel_compose["services"].keys()) == {"beszel", "beszel-agent"}

    def test_socket_volume_defined(self, beszel_compose: dict[str, Any]) -> None:
        assert "beszel-socket" in beszel_compose.get("volumes", {})


class TestUptimeKumaDockerCompose:
    def test_uptime_kuma_service_present(
        self, uptime_kuma_compose: dict[str, Any]
    ) -> None:
        assert "uptime-kuma" in uptime_kuma_compose["services"]
