from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

TRAEFIK_SERVICE_PATH = SERVICES_PATH / "traefik"
TRAEFIK_COMPOSE_PATH = TRAEFIK_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(TRAEFIK_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestTraefikDockerCompose:
    def test_no_new_privileges(self, compose_config: dict[str, Any]) -> None:
        security_opt = compose_config["services"]["traefik"].get("security_opt", [])
        assert "no-new-privileges:true" in security_opt

    def test_docker_socket_readonly(self, compose_config: dict[str, Any]) -> None:
        volumes = compose_config["services"]["traefik"]["volumes"]
        docker_sock_mounts = [v for v in volumes if "docker.sock" in v]
        assert len(docker_sock_mounts) > 0, "Docker socket not mounted"
        assert all(":ro" in v for v in docker_sock_mounts), (
            "Docker socket must be mounted read-only"
        )

    def test_ports_80_and_443_exposed(self, compose_config: dict[str, Any]) -> None:
        ports = compose_config["services"]["traefik"]["ports"]
        port_strings = [str(p) for p in ports]
        assert any("80:80" in p for p in port_strings), "Port 80 not exposed"
        assert any("443:443" in p for p in port_strings), "Port 443 not exposed"
