from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

BACKUPS_SERVICE_PATH = SERVICES_PATH / "backups"
BACKUPS_COMPOSE_PATH = BACKUPS_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(BACKUPS_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestBackupsDockerCompose:
    def test_container_name_is_backrest(self, compose_config: dict[str, Any]) -> None:
        assert compose_config["services"]["backrest"]["container_name"] == "backrest"

    def test_image_is_backrest(self, compose_config: dict[str, Any]) -> None:
        image = compose_config["services"]["backrest"]["image"]
        assert image == "ghcr.io/garethgeorge/backrest:latest"

    def test_required_env_vars_present(self, compose_config: dict[str, Any]) -> None:
        env = compose_config["services"]["backrest"]["environment"]
        env_keys = [e.split("=")[0] for e in env]
        required = (
            "RESTIC_PASSWORD",
            "BACKREST_DATA",
            "BACKREST_CONFIG",
            "BACKREST_PORT",
        )
        for var in required:
            assert var in env_keys, f"Missing required env var: {var}"

    def test_volume_mounts(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["backrest"]["volumes"]
        assert any("/config" in v for v in volumes)
        assert any("/data" in v for v in volumes)
        assert any("/cache" in v for v in volumes)
        assert any("rclone" in v and ":ro" in v for v in volumes)
        assert any("/userdata" in v and ":ro" in v for v in volumes)
        assert any("/repos" in v for v in volumes)

    def test_memory_limits_set(self, compose_config: dict[str, Any]) -> None:
        resources = compose_config["services"]["backrest"]["deploy"]["resources"]
        assert resources["limits"]["memory"] == "512M"
        assert resources["reservations"]["memory"] == "256M"

    def test_traefik_labels_present(self, compose_config: dict[str, Any]) -> None:
        labels = compose_config["services"]["backrest"]["labels"]
        assert any("traefik.enable=true" in label for label in labels)
        assert any("backups.${DOMAIN}" in label for label in labels)

    def test_healthcheck_configured(self, compose_config: dict[str, Any]) -> None:
        healthcheck = compose_config["services"]["backrest"]["healthcheck"]
        assert healthcheck is not None
        assert "test" in healthcheck
