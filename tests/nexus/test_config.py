from nexus.config import PRESETS, get_base_domain, resolve_preset


def test_presets_exist():
    assert "core" in PRESETS
    assert "home" in PRESETS


def test_resolve_preset_core():
    services = resolve_preset("core")
    assert "traefik" in services
    assert "auth" in services
    assert "dashboard" in services
    assert "monitoring" in services


def test_resolve_preset_home():
    services = resolve_preset("home")
    assert "traefik" in services
    assert "auth" in services
    assert "dashboard" in services
    assert "monitoring" in services
    assert "sure" in services
    assert "foundryvtt" in services
    assert "jellyfin" in services
    assert "transmission" in services
    assert "backups" in services


def test_resolve_preset_invalid():
    services = resolve_preset("invalid")
    assert services == []


def test_get_base_domain(monkeypatch):
    monkeypatch.setenv("NEXUS_DOMAIN", "example.com")
    assert get_base_domain() == "example.com"


def test_get_base_domain_not_set(monkeypatch):
    monkeypatch.delenv("NEXUS_DOMAIN", raising=False)
    assert get_base_domain() is None


def test_all_services_path_exists():
    from nexus.config import SERVICES_PATH

    assert SERVICES_PATH.exists()
