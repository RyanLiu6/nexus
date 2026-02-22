import pytest

from nexus.config import get_base_domain, load_presets, resolve_preset


class TestPresets:
    def test_presets_exist(self) -> None:
        presets = load_presets()
        assert "core" in presets
        assert "home" in presets

    def test_resolve_preset(self) -> None:
        services = resolve_preset("core")
        assert "traefik" in services
        assert "tailscale-access" in services
        assert "dashboard" in services
        assert "monitoring" in services

    def test_resolve_preset_home_inherits_core(self) -> None:
        services = resolve_preset("home")
        assert "traefik" in services
        assert "tailscale-access" in services
        assert "dashboard" in services
        assert "monitoring" in services

    def test_resolve_preset_home_includes_additional_services(self) -> None:
        services = resolve_preset("home")
        assert "sure" in services
        assert "foundryvtt" in services
        assert "jellyfin" in services
        assert "transmission" in services
        assert "backups" in services
        assert "paperless" in services
        assert "booklore" in services

    def test_resolve_preset_invalid_returns_empty(self) -> None:
        services = resolve_preset("invalid")
        assert services == []


class TestGetBaseDomain:
    def test_get_base_domain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NEXUS_DOMAIN", "example.com")
        assert get_base_domain() == "example.com"

    def test_get_base_domain_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NEXUS_DOMAIN", raising=False)
        assert get_base_domain() is None


class TestPaths:
    def test_services_path_exists(self) -> None:
        from nexus.config import SERVICES_PATH

        assert SERVICES_PATH.exists()
