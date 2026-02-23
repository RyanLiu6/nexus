from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

MONITORING_SERVICE_PATH = SERVICES_PATH / "monitoring"
MONITORING_COMPOSE_PATH = MONITORING_SERVICE_PATH / "docker-compose.yml"

_EXPECTED_CONTAINERS = {
    "node-exporter",
    "prometheus",
    "grafana",
    "alertmanager",
    "alert-bot",
    "tailscale-exporter",
}

_NAMED_VOLUMES = ["prometheus-data", "grafana-data", "alertmanager-data"]


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(MONITORING_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestMonitoringDockerCompose:
    def test_all_six_containers_present(self, compose_config: dict[str, Any]) -> None:
        assert set(compose_config["services"].keys()) == _EXPECTED_CONTAINERS

    @pytest.mark.parametrize("volume_name", _NAMED_VOLUMES)
    def test_named_volume_defined(
        self, compose_config: dict[str, Any], volume_name: str
    ) -> None:
        assert volume_name in compose_config.get("volumes", {}), (
            f"Named volume '{volume_name}' not defined"
        )

    def test_alert_bot_uses_build(self, compose_config: dict[str, Any]) -> None:
        alert_bot = compose_config["services"]["alert-bot"]
        assert "build" in alert_bot, "alert-bot should use build directive, not image"
        assert "image" not in alert_bot

    def test_tailscale_exporter_uses_build(
        self, compose_config: dict[str, Any]
    ) -> None:
        exporter = compose_config["services"]["tailscale-exporter"]
        assert "build" in exporter, (
            "tailscale-exporter should use build directive, not image"
        )
        assert "image" not in exporter
