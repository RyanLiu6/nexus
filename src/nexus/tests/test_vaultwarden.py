from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH
from nexus.services import ServiceManifest

VAULTWARDEN_SERVICE_PATH = SERVICES_PATH / "vaultwarden"
VAULTWARDEN_MANIFEST_PATH = VAULTWARDEN_SERVICE_PATH / "service.yml"
VAULTWARDEN_COMPOSE_PATH = VAULTWARDEN_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    """Load and parse the Vaultwarden docker-compose.yml file.

    Returns:
        Parsed docker-compose.yml as a dictionary.
    """
    with open(VAULTWARDEN_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestVaultwardenServiceManifest:
    def test_service_manifest_exists(self) -> None:
        assert VAULTWARDEN_MANIFEST_PATH.exists()

    def test_service_manifest_access_admins_only(self) -> None:
        manifest = ServiceManifest.from_yaml(VAULTWARDEN_MANIFEST_PATH)
        assert "admins" in manifest.access_groups
        assert len(manifest.access_groups) == 1

    def test_service_manifest_not_public(self) -> None:
        manifest = ServiceManifest.from_yaml(VAULTWARDEN_MANIFEST_PATH)
        assert manifest.is_public is False

    def test_service_manifest_dependencies(self) -> None:
        manifest = ServiceManifest.from_yaml(VAULTWARDEN_MANIFEST_PATH)
        assert "traefik" in manifest.dependencies
        assert "tailscale-access" in manifest.dependencies


class TestVaultwardenDockerCompose:
    def test_docker_compose_exists(self) -> None:
        assert VAULTWARDEN_COMPOSE_PATH.exists()

    def test_docker_compose_tailscale_middleware(
        self, compose_config: dict[str, Any]
    ) -> None:
        labels = compose_config["services"]["vaultwarden"]["labels"]
        middleware_labels = [
            label
            for label in labels
            if "middlewares" in label and "tailscale-chain" in label
        ]
        assert len(middleware_labels) > 0

    def test_docker_compose_https_only(self, compose_config: dict[str, Any]) -> None:
        labels = compose_config["services"]["vaultwarden"]["labels"]
        entrypoint_labels = [label for label in labels if "entrypoints=https" in label]
        assert len(entrypoint_labels) > 0

    def test_docker_compose_signups_disabled(
        self, compose_config: dict[str, Any]
    ) -> None:
        env_vars = compose_config["services"]["vaultwarden"]["environment"]
        signups_var = next(
            (var for var in env_vars if var.startswith("SIGNUPS_ALLOWED=")), None
        )
        assert signups_var is not None
        assert "false" in signups_var.lower()

    def test_docker_compose_admin_token_required(
        self, compose_config: dict[str, Any]
    ) -> None:
        env_vars = compose_config["services"]["vaultwarden"]["environment"]
        admin_token_vars = [var for var in env_vars if "ADMIN_TOKEN=" in var]
        assert len(admin_token_vars) > 0

    def test_docker_compose_security_opts(self, compose_config: dict[str, Any]) -> None:
        security_opt = compose_config["services"]["vaultwarden"].get("security_opt", [])
        assert "no-new-privileges:true" in security_opt

    def test_docker_compose_healthcheck(self, compose_config: dict[str, Any]) -> None:
        healthcheck = compose_config["services"]["vaultwarden"].get("healthcheck")
        assert healthcheck is not None
        assert "test" in healthcheck
        assert "interval" in healthcheck

    def test_docker_compose_resource_limits(
        self, compose_config: dict[str, Any]
    ) -> None:
        deploy = compose_config["services"]["vaultwarden"].get("deploy")
        assert deploy is not None
        assert "resources" in deploy
        assert "limits" in deploy["resources"]
        assert "memory" in deploy["resources"]["limits"]


class TestVaultwardenSecurityHardening:
    @pytest.mark.parametrize(
        "env_var_prefix",
        [
            "SHOW_PASSWORD_HINT=",
            "PASSWORD_HINTS_ALLOWED=",
        ],
    )
    def test_password_hints_disabled(
        self, compose_config: dict[str, Any], env_var_prefix: str
    ) -> None:
        env_vars = compose_config["services"]["vaultwarden"]["environment"]
        env_var = next(
            (var for var in env_vars if var.startswith(env_var_prefix)), None
        )
        assert env_var is not None
        assert "false" in env_var.lower()

    @pytest.mark.parametrize(
        "env_var_prefix,expected_value",
        [
            ("LOGIN_RATELIMIT_SECONDS=", "60"),
            ("LOGIN_RATELIMIT_MAX_BURST=", "10"),
            ("ADMIN_RATELIMIT_SECONDS=", "300"),
            ("ADMIN_RATELIMIT_MAX_BURST=", "3"),
        ],
    )
    def test_rate_limiting(
        self, compose_config: dict[str, Any], env_var_prefix: str, expected_value: str
    ) -> None:
        env_vars = compose_config["services"]["vaultwarden"]["environment"]
        env_var = next(
            (var for var in env_vars if var.startswith(env_var_prefix)), None
        )
        assert env_var is not None
        assert expected_value in env_var

    def test_admin_session_lifetime(self, compose_config: dict[str, Any]) -> None:
        env_vars = compose_config["services"]["vaultwarden"]["environment"]

        session_lifetime = next(
            (var for var in env_vars if var.startswith("ADMIN_SESSION_LIFETIME=")),
            None,
        )

        assert session_lifetime is not None
        assert "20" in session_lifetime
