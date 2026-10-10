from pathlib import Path

from nexus.services import (
    ServiceManifest,
    discover_services,
    get_all_service_names,
    resolve_dependencies,
)


class TestServiceManifest:
    def test_from_yaml(self, tmp_path: Path) -> None:
        manifest_content = """
name: test-service
description: A test service
subdomain: test

dependencies:
  - traefik
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)

        assert manifest.name == "test-service"
        assert manifest.description == "A test service"
        assert manifest.subdomains == ["test"]
        assert manifest.dependencies == ["traefik"]

    def test_from_yaml_multiple_subdomains(self, tmp_path: Path) -> None:
        manifest_content = """
name: monitoring
description: Monitoring stack
subdomains:
  - grafana
  - prometheus
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)

        assert manifest.subdomains == ["grafana", "prometheus"]

    def test_has_web_access_with_subdomain(self, tmp_path: Path) -> None:
        manifest_content = """
name: web-service
description: Has web
subdomain: web
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)
        assert manifest.has_web_access() is True

    def test_has_web_access_no_subdomain(self, tmp_path: Path) -> None:
        manifest_content = """
name: internal-service
description: No web
subdomain: null
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)
        assert manifest.has_web_access() is False


class TestDiscoverServices:
    def test_discover_services(self) -> None:
        services = discover_services()
        assert isinstance(services, dict)
        assert len(services) > 0

    def test_discover_services_includes_known_services(self) -> None:
        services = discover_services()
        assert "traefik" in services
        assert "plex" in services
        assert "monitoring" in services

    def test_discover_services_includes_new_services(self) -> None:
        services = discover_services()
        assert "paperless" in services
        assert "bookorbit" in services

    def test_get_all_service_names(self) -> None:
        names = get_all_service_names()
        assert isinstance(names, list)
        assert names == sorted(names)
        assert "traefik" in names


class TestResolveDependencies:
    def test_resolve_dependencies(self) -> None:
        all_services = discover_services()
        resolved = resolve_dependencies(["plex"], all_services)

        assert "plex" in resolved
        assert "traefik" in resolved
        assert "authentik" in resolved

    def test_resolve_dependencies_no_dependencies(self) -> None:
        all_services = discover_services()
        resolved = resolve_dependencies(["traefik"], all_services)

        assert "traefik" in resolved
        assert len(resolved) >= 1

    def test_resolve_dependencies_deduplicates(self) -> None:
        all_services = discover_services()
        resolved = resolve_dependencies(["plex", "sure", "traefik"], all_services)

        assert len(resolved) == len(set(resolved))
