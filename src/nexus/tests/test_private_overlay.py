from nexus.config import (
    PRIVATE_ROOT_PATH,
    PRIVATE_SERVICES_PATH,
    load_presets,
    resolve_preset,
)
from nexus.services import discover_services


def test_private_paths_detected() -> None:
    """Verify that the private repo is detected if present in ~/dev/nexus-private."""
    if PRIVATE_ROOT_PATH:
        assert PRIVATE_ROOT_PATH.exists()
        assert PRIVATE_ROOT_PATH.is_dir()
        if PRIVATE_SERVICES_PATH:
            assert PRIVATE_SERVICES_PATH.exists()
            assert PRIVATE_SERVICES_PATH.is_dir()


def test_discover_services_finds_amane() -> None:
    """Verify that discover_services includes amane from nexus-private."""
    services = discover_services()
    if PRIVATE_SERVICES_PATH and (PRIVATE_SERVICES_PATH / "amane").exists():
        assert "amane" in services
        manifest = services["amane"]
        assert manifest.name == "amane"
        assert manifest.subdomains == ["amane"]
        assert manifest.path == PRIVATE_SERVICES_PATH / "amane"


def test_presets_merge_private_services() -> None:
    """Verify that load_presets merges presets from nexus-private."""
    # Clear cache to get fresh presets
    load_presets.cache_clear()
    presets = load_presets()

    if PRIVATE_ROOT_PATH and (PRIVATE_ROOT_PATH / "config" / "presets.yml").exists():
        assert "private" in presets
        resolved_private = resolve_preset("private")
        assert "amane" in resolved_private

        resolved_home = resolve_preset("home")
        assert "amane" in resolved_home
        # Verify public home services are also preserved
        assert "jellyfin" in resolved_home
