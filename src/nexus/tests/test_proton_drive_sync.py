from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH
from nexus.services import ServiceManifest

PROTON_DRIVE_SYNC_SERVICE_PATH = SERVICES_PATH / "proton-drive-sync"
PROTON_DRIVE_SYNC_COMPOSE_PATH = PROTON_DRIVE_SYNC_SERVICE_PATH / "docker-compose.yml"
PROTON_DRIVE_SYNC_SERVICE_YML_PATH = PROTON_DRIVE_SYNC_SERVICE_PATH / "service.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(PROTON_DRIVE_SYNC_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestProtonDriveSyncDockerCompose:
    def test_memory_limits_set(self, compose_config: dict[str, Any]) -> None:
        resources = compose_config["services"]["proton-drive-sync"]["deploy"][
            "resources"
        ]
        assert resources["limits"]["memory"] == "512M"
        assert resources["reservations"]["memory"] == "128M"

    def test_paperless_documents_volume_readonly(
        self, compose_config: dict[str, Any]
    ) -> None:
        volumes = compose_config["services"]["proton-drive-sync"]["volumes"]
        assert any("PAPERLESS_DOCUMENTS_DIRECTORY" in v and ":ro" in v for v in volumes)

    def test_backups_volume_readonly(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["proton-drive-sync"]["volumes"]
        assert any("/Backups" in v and ":ro" in v for v in volumes)

    def test_on_nexus_network(self, compose_config: dict[str, Any]) -> None:
        networks = compose_config["services"]["proton-drive-sync"]["networks"]
        assert "nexus" in networks

    def test_nexus_network_is_external(self, compose_config: dict[str, Any]) -> None:
        networks = compose_config["networks"]
        assert networks["nexus"]["external"] is True

    def test_traefik_labels_present(self, compose_config: dict[str, Any]) -> None:
        labels = compose_config["services"]["proton-drive-sync"]["labels"]
        assert any("traefik.enable=true" in label for label in labels)
        assert any("protondrive.${NEXUS_DOMAIN}" in label for label in labels)
        assert any("entrypoints=https" in label for label in labels)
        assert any("certresolver=certchallenge" in label for label in labels)
        assert any("tailscale-chain" in label for label in labels)


class TestProtonDriveSyncServiceManifest:
    def test_service_yml_exists(self) -> None:
        assert PROTON_DRIVE_SYNC_SERVICE_YML_PATH.exists()

    def test_service_manifest_metadata(self) -> None:
        manifest = ServiceManifest.from_yaml(PROTON_DRIVE_SYNC_SERVICE_YML_PATH)
        assert manifest.name == "proton-drive-sync"
        assert manifest.access_groups == ["admins"]
        assert manifest.is_public is False
        assert "traefik" in manifest.dependencies
        assert "tailscale-access" in manifest.dependencies
