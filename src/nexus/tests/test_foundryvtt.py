from typing import Any

import pytest
import yaml

from nexus.config import SERVICES_PATH

FOUNDRYVTT_SERVICE_PATH = SERVICES_PATH / "foundryvtt"
FOUNDRYVTT_COMPOSE_PATH = FOUNDRYVTT_SERVICE_PATH / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict[str, Any]:
    with open(FOUNDRYVTT_COMPOSE_PATH) as f:
        return dict(yaml.safe_load(f))


class TestFoundryvttDockerCompose:
    def test_dual_router_setup(self, compose_config: dict[str, Any]) -> None:
        labels = compose_config["services"]["foundryvtt"]["labels"]
        has_http_router = any("entrypoints=http" in label for label in labels)
        has_https_router = any("entrypoints=https" in label for label in labels)
        assert has_http_router, "Missing HTTP router (for Cloudflare Tunnel)"
        assert has_https_router, "Missing HTTPS router"

    def test_cloudflare_middleware_on_http_router(
        self, compose_config: dict[str, Any]
    ) -> None:
        labels = compose_config["services"]["foundryvtt"]["labels"]
        cloudflare_labels = [
            label for label in labels if "cloudflare-proto@file" in label
        ]
        assert len(cloudflare_labels) > 0, (
            "HTTP router missing cloudflare-proto@file middleware"
        )

    def test_no_tailscale_chain_on_https_router(
        self, compose_config: dict[str, Any]
    ) -> None:
        labels = compose_config["services"]["foundryvtt"]["labels"]
        # The secure (https) router must NOT have tailscale-chain (it's public access)
        secure_middleware_labels = [
            label
            for label in labels
            if "foundryvtt-secure" in label and "middlewares" in label
        ]
        assert len(secure_middleware_labels) > 0, "HTTPS router has no middleware label"
        for label in secure_middleware_labels:
            assert "tailscale-chain" not in label, (
                "HTTPS router should not use tailscale-chain "
                "(FoundryVTT is public access)"
            )
