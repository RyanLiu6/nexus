"""Tests for service discovery and manifest parsing."""

from pathlib import Path

from nexus.services import (
    ServiceManifest,
    discover_services,
    get_all_service_names,
    get_public_services,
    get_services_by_category,
    resolve_dependencies,
)


class TestServiceManifest:
    def test_from_yaml_basic(self, tmp_path: Path) -> None:
        manifest_content = """
name: test-service
description: A test service
category: core
subdomain: test

access:
  groups: [admins]
  public: false

dependencies:
  - traefik
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)

        assert manifest.name == "test-service"
        assert manifest.description == "A test service"
        assert manifest.category == "core"
        assert manifest.subdomains == ["test"]
        assert manifest.access_groups == ["admins"]
        assert manifest.is_public is False
        assert manifest.dependencies == ["traefik"]

    def test_from_yaml_multiple_subdomains(self, tmp_path: Path) -> None:
        manifest_content = """
name: monitoring
description: Monitoring stack
category: core
subdomains:
  - grafana
  - prometheus

access:
  groups: [admins]
  public: false
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)

        assert manifest.subdomains == ["grafana", "prometheus"]

    def test_from_yaml_public_service(self, tmp_path: Path) -> None:
        manifest_content = """
name: public-app
description: Public app
category: apps
subdomain: app

access:
  groups: [admins, members]
  public: true

dependencies: []
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)

        assert manifest.is_public is True
        assert manifest.access_groups == ["admins", "members"]

    def test_has_web_access_with_subdomain(self, tmp_path: Path) -> None:
        manifest_content = """
name: web-service
description: Has web
category: core
subdomain: web
access:
  groups: [admins]
  public: false
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)
        assert manifest.has_web_access() is True

    def test_has_web_access_no_subdomain(self, tmp_path: Path) -> None:
        manifest_content = """
name: internal-service
description: No web
category: core
subdomain: null
access:
  groups: []
  public: false
"""
        manifest_path = tmp_path / "service.yml"
        manifest_path.write_text(manifest_content)

        manifest = ServiceManifest.from_yaml(manifest_path)
        assert manifest.has_web_access() is False


class TestDiscoverServices:
    def test_discover_services_returns_dict(self) -> None:
        """Test that discover_services returns a dictionary."""
        services = discover_services()
        assert isinstance(services, dict)
        assert len(services) > 0

    def test_discover_services_includes_known_services(self) -> None:
        """Test expected services are discovered."""
        services = discover_services()
        assert "traefik" in services
        assert "dashboard" in services
        assert "monitoring" in services

    def test_get_all_service_names(self) -> None:
        """Test that get_all_service_names returns sorted list."""
        names = get_all_service_names()
        assert isinstance(names, list)
        assert names == sorted(names)
        assert "traefik" in names


class TestGetServicesByCategory:
    def test_returns_dict_of_lists(self) -> None:
        by_category = get_services_by_category()
        assert isinstance(by_category, dict)
        for _category, services in by_category.items():
            assert isinstance(services, list)
            for svc in services:
                assert isinstance(svc, ServiceManifest)

    def test_expected_categories_exist(self) -> None:
        by_category = get_services_by_category()
        # At minimum we should have these categories
        assert "core" in by_category
        assert "apps" in by_category or "media" in by_category


class TestGetPublicServices:
    def test_returns_list(self) -> None:
        public = get_public_services()
        assert isinstance(public, list)

    def test_only_public_services(self) -> None:
        public = get_public_services()
        for svc in public:
            assert svc.is_public is True


class TestResolveDependencies:
    def test_resolves_simple_dependency(self) -> None:
        all_services = discover_services()
        resolved = resolve_dependencies(["dashboard"], all_services)

        assert "dashboard" in resolved
        # Dashboard depends on traefik and tailscale-access
        assert "traefik" in resolved
        assert "tailscale-access" in resolved

    def test_handles_no_dependencies(self) -> None:
        all_services = discover_services()
        resolved = resolve_dependencies(["traefik"], all_services)

        assert "traefik" in resolved
        # Traefik has no dependencies, so only itself
        assert len(resolved) >= 1

    def test_deduplicates(self) -> None:
        all_services = discover_services()
        resolved = resolve_dependencies(["dashboard", "sure", "traefik"], all_services)

        # Should not have duplicates
        assert len(resolved) == len(set(resolved))
