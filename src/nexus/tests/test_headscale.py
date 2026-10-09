from typing import Any

import pytest
import yaml

from nexus.services import discover_services

HEADSCALE_SERVICE_PATH = discover_services()["headscale"].path
HEADSCALE_COMPOSE_PATH = HEADSCALE_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(HEADSCALE_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestHeadscaleManifest:
    def test_manifest_exists(self) -> None:
        manifest = discover_services()["headscale"]
        assert manifest.name == "headscale"
        assert manifest.category == "core"

    def test_depends_on_traefik(self) -> None:
        manifest = discover_services()["headscale"]
        assert "traefik" in manifest.dependencies

    def test_is_public(self) -> None:
        manifest = discover_services()["headscale"]
        assert manifest.is_public is True

    def test_subdomains(self) -> None:
        manifest = discover_services()["headscale"]
        assert manifest.subdomains == ["headscale", "headplane"]


class TestHeadscaleDockerCompose:
    def test_container_configuration(self, compose_config: dict[str, Any]) -> None:
        services = compose_config.get("services", {})
        assert "headscale" in services
        headscale = services["headscale"]
        assert headscale["container_name"] == "headscale"
        assert headscale["restart"] == "unless-stopped"
        assert headscale["command"] == "serve"

    def test_stun_port_exposed(self, compose_config: dict[str, Any]) -> None:
        ports = compose_config["services"]["headscale"].get("ports", [])
        port_strings = [str(p) for p in ports]
        assert any("26478:26478/udp" in p for p in port_strings), (
            "STUN port 26478/udp must be exposed"
        )

    def test_volume_mounts(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["headscale"].get("volumes", [])
        assert any("config.yaml" in v for v in volumes), "config.yaml must be mounted"
        assert any("acl.hujson" in v for v in volumes), "acl.hujson must be mounted"
        assert any("headscale" in v and "/var/lib/headscale" in v for v in volumes), (
            "data dir must be mounted"
        )

    def test_no_tailscale_chain_on_routers(
        self, compose_config: dict[str, Any]
    ) -> None:
        labels = compose_config["services"]["headscale"].get("labels", [])
        for label in labels:
            assert "tailscale-chain" not in label, (
                "Headscale routers must not use tailscale-chain"
            )

    def test_healthcheck_defined(self, compose_config: dict[str, Any]) -> None:
        healthcheck = compose_config["services"]["headscale"].get("healthcheck", {})
        assert "test" in healthcheck

    def test_headplane_service(self, compose_config: dict[str, Any]) -> None:
        services = compose_config.get("services", {})
        assert "headplane" in services
        headplane = services["headplane"]
        assert headplane["container_name"] == "headplane"
        labels = headplane.get("labels", [])
        assert any("tailscale-chain@file" in label for label in labels), (
            "Headplane must be protected by tailscale-chain"
        )
