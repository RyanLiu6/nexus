from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexus.generate.dashboard import (
    categorize_service,
    generate_bookmarks_config,
    generate_dashboard_config,
    generate_settings_config,
    generate_widgets_config,
    get_service_config,
    get_service_description,
    get_service_icon,
)


class TestGetServiceDescription:
    @pytest.mark.parametrize(
        "service,expected",
        [
            ("traefik", "Reverse proxy with automatic SSL"),
            ("dashboard", "Service dashboard and homepage"),
            ("sure-web", "Finance and budgeting"),
            ("foundryvtt", "Virtual tabletop for D&D"),
            ("jellyfin", "Media server for movies and TV"),
            ("transmission", "Torrent download client"),
            ("unknown", ""),
        ],
    )
    def test_get_service_description(self, service: str, expected: str) -> None:
        assert get_service_description(service) == expected


class TestGetServiceIcon:
    @pytest.mark.parametrize(
        "service,expected",
        [
            ("traefik", "si-traefikproxy"),
            ("dashboard", "si-homeassistant"),
            ("plex", "si-plex"),
            ("jellyfin", "si-jellyfin"),
            ("transmission", "si-transmission"),
            ("prometheus", "si-prometheus"),
            ("grafana", "si-grafana"),
            ("alertmanager", "si-prometheus"),
            ("unknown", "mdi-application"),
        ],
    )
    def test_get_service_icon(self, service: str, expected: str) -> None:
        assert get_service_icon(service) == expected


class TestCategorizeService:
    @pytest.mark.parametrize(
        "service,expected",
        [
            ("traefik", "Core"),
            ("dashboard", "Core"),
            ("prometheus", "Core"),
            ("grafana", "Core"),
            ("alertmanager", "Core"),
            ("plex", "Media"),
            ("jellyfin", "Media"),
            ("transmission", "Media"),
            ("sure-web", "Apps"),
            ("foundryvtt", "Apps"),
            ("nextcloud", "Apps"),
            ("unknown", "Other"),
        ],
    )
    def test_categorize_service(self, service: str, expected: str) -> None:
        assert categorize_service(service) == expected


class TestGetServiceConfig:
    @patch("nexus.generate.dashboard.SERVICES_PATH")
    def test_get_service_config_missing_file(
        self, mock_path: MagicMock, tmp_path: Path
    ) -> None:
        mock_path.__truediv__.return_value = tmp_path / "missing"

        result = get_service_config("missing")

        assert result == []

    @patch("nexus.generate.dashboard.SERVICES_PATH")
    def test_get_service_config_with_list_labels(
        self, mock_path: MagicMock, tmp_path: Path
    ) -> None:
        service_dir = tmp_path / "plex"
        service_dir.mkdir()
        compose_file = service_dir / "docker-compose.yml"
        compose_file.write_text("""
services:
  plex:
    image: linuxserver/plex
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.plex.rule=Host(`plex.example.com`)"
""")

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_path.__truediv__.side_effect = path_side_effect

        result = get_service_config("plex")

        assert len(result) == 1
        assert result[0]["name"] == "plex"
        assert result[0]["container"] == "plex"
        assert "plex.example.com" in result[0]["rule"]

    @patch("nexus.generate.dashboard.SERVICES_PATH")
    def test_get_service_config_multiple_services(
        self, mock_path: MagicMock, tmp_path: Path
    ) -> None:
        service_dir = tmp_path / "monitoring"
        service_dir.mkdir()
        compose_file = service_dir / "docker-compose.yml"
        compose_file.write_text("""
services:
  prometheus:
    image: prom/prometheus
    labels:
      - "traefik.http.routers.prometheus.rule=Host(`prom.example.com`)"
  grafana:
    image: grafana/grafana
    labels:
      - "traefik.http.routers.grafana.rule=Host(`grafana.example.com`)"
""")

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_path.__truediv__.side_effect = path_side_effect

        result = get_service_config("monitoring")

        assert len(result) == 2
        names = {s["name"] for s in result}
        assert "prometheus" in names
        assert "grafana" in names

    @patch("nexus.generate.dashboard.SERVICES_PATH")
    def test_get_service_config_no_traefik_labels(
        self, mock_path: MagicMock, tmp_path: Path
    ) -> None:
        service_dir = tmp_path / "redis"
        service_dir.mkdir()
        compose_file = service_dir / "docker-compose.yml"
        compose_file.write_text("""
services:
  redis:
    image: redis:alpine
""")

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_path.__truediv__.side_effect = path_side_effect

        result = get_service_config("redis")

        assert result == []


class TestGenerateDashboardConfig:
    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config(self, mock_get_config: MagicMock) -> None:
        mock_get_config.side_effect = [
            [
                {
                    "name": "plex",
                    "container": "plex",
                    "rule": "Host(`plex.example.com`)",
                    "description": "Media streaming",
                    "icon": "si-plex",
                }
            ],
            [
                {
                    "name": "jellyfin",
                    "container": "jellyfin",
                    "rule": "Host(`jellyfin.example.com`)",
                    "description": "Media server",
                    "icon": "si-jellyfin",
                }
            ],
        ]

        result = generate_dashboard_config(["plex", "jellyfin"], "example.com")

        media_category = next((item for item in result if "Media" in item), None)
        assert media_category is not None
        assert len(media_category["Media"]) == 2

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_skips_dashboard(
        self, mock_get_config: MagicMock
    ) -> None:
        result = generate_dashboard_config(["dashboard"], "example.com")

        weather_group = next((c["Weather"] for c in result if "Weather" in c), None)
        assert weather_group is None

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_skips_empty(
        self, mock_get_config: MagicMock
    ) -> None:
        mock_get_config.return_value = []

        result = generate_dashboard_config(["missing"], "example.com")

        weather_group = next((c["Weather"] for c in result if "Weather" in c), None)
        assert weather_group is None

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_fallback_url(
        self, mock_get_config: MagicMock
    ) -> None:
        mock_get_config.return_value = [
            {
                "name": "plex",
                "container": "plex",
                "rule": "PathPrefix(`/plex`)",
                "description": "Media streaming",
                "icon": "si-plex",
            }
        ]

        result = generate_dashboard_config(["plex"], "example.com")

        media_category = next((item for item in result if "Media" in item), None)
        assert media_category is not None
        assert media_category["Media"][0]["plex"]["href"] == "https://plex.example.com"

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_with_widgets(
        self, mock_get_config: MagicMock
    ) -> None:
        mock_get_config.side_effect = lambda name: [
            {
                "name": name,
                "container": name,
                "rule": f"Host(`{name}.example.com`)",
                "description": "desc",
                "icon": "icon.png",
            }
        ]

        secrets = {
            "grafana_admin_password": "secret",
            "jellyfin_api_key": "jellykey",
        }

        # Test with services that have widgets
        services = ["traefik", "grafana", "jellyfin"]
        config = generate_dashboard_config(services, "example.com", secrets=secrets)

        core_group = next((c["Core"] for c in config if "Core" in c), None)
        assert core_group is not None
        traefik = next((i["traefik"] for i in core_group if "traefik" in i), None)
        assert traefik is not None
        assert "widget" in traefik
        assert traefik["widget"]["type"] == "traefik"
        assert traefik["widget"]["url"] == "http://traefik:8080"

        grafana = next((i["grafana"] for i in core_group if "grafana" in i), None)
        assert grafana is not None
        assert grafana["widget"]["username"] == "admin"
        assert grafana["widget"]["password"] == "secret"

        media_group = next((c["Media"] for c in config if "Media" in c), None)
        assert media_group is not None
        jellyfin = next((i["jellyfin"] for i in media_group if "jellyfin" in i), None)
        assert jellyfin is not None
        assert jellyfin["widget"]["key"] == "jellykey"

    def test_generate_dashboard_config_missing_secrets(self) -> None:
        with patch("nexus.generate.dashboard.get_service_config") as mock_get:
            mock_get.return_value = [
                {
                    "name": "jellyfin",
                    "container": "jellyfin",
                    "description": "desc",
                    "icon": "icon",
                }
            ]
            config = generate_dashboard_config(["jellyfin"], "example.com", secrets={})

            media_group = next((c["Media"] for c in config if "Media" in c), None)
            assert media_group is not None
            jellyfin = next(
                (i["jellyfin"] for i in media_group if "jellyfin" in i), None
            )
            assert jellyfin is not None
            assert "widget" not in jellyfin

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_domain_substitution(
        self, mock_get_config: MagicMock
    ) -> None:
        mock_get_config.return_value = [
            {
                "name": "foundryvtt",
                "container": "foundryvtt",
                "rule": "Host(`foundry.${NEXUS_DOMAIN}`)",
                "description": "Virtual Tabletop",
                "icon": "si-foundryvirtualtabletop",
            }
        ]

        result = generate_dashboard_config(["foundryvtt"], "my-domain.com")

        apps_category = next((item for item in result if "Apps" in item), None)
        assert apps_category is not None
        href = apps_category["Apps"][0]["foundryvtt"]["href"]
        assert href == "https://foundry.my-domain.com"


class TestGenerateSettingsConfig:
    def test_generate_settings_config(self) -> None:
        config = generate_settings_config()

        assert config["title"] == "Nexus"
        assert "theme" not in config
        assert config["color"] == "slate"
        assert config["background"]["image"] == "/images/background.png"
        assert config["background"]["opacity"] == 30
        assert config["cardBlur"] == "md"
        assert config["statusStyle"] == "dot"
        layout = config["layout"]
        assert "Weather" not in layout
        assert layout["Media"] == {"style": "row", "columns": 2}
        assert layout["Core"] == {"style": "row", "columns": 2}
        assert config["hideVersion"] is True

    def test_generate_settings_config_quicklaunch(self) -> None:
        config = generate_settings_config()

        assert "quicklaunch" not in config


class TestGenerateBookmarksConfig:
    def test_generate_bookmarks_config(self) -> None:
        config = generate_bookmarks_config()

        assert isinstance(config, list)

        prod_section = next((item for item in config if "Productivity" in item), None)
        assert prod_section is not None

        items = prod_section["Productivity"]
        assert any("Github" in item for item in items)
        assert any("Gmail" in item for item in items)
        assert any("ProtonMail" in item for item in items)
        assert any("Cloudflare" in item for item in items)


class TestGenerateWidgetsConfig:
    def test_generate_widgets_config(self) -> None:
        config = generate_widgets_config()

        assert isinstance(config, list)
        assert len(config) == 3

        widget_types = [next(iter(w.keys())) for w in config]
        assert "datetime" in widget_types
        assert "openmeteo" in widget_types
        assert "resources" in widget_types

        resources = next((w for w in config if "resources" in w), None)
        assert resources is not None
        assert resources["resources"]["cpu"] is True
        assert resources["resources"]["memory"] is True
        assert resources["resources"]["disk"] == "/"

        weather = next((w for w in config if "openmeteo" in w), None)
        assert weather is not None
        assert weather["openmeteo"]["label"] == "Weather"

    def test_generate_widgets_config_custom_location(self) -> None:
        config = generate_widgets_config(
            latitude=51.5074,
            longitude=-0.1278,
            timezone="Europe/London",
            units="imperial",
        )

        weather = next((w for w in config if "openmeteo" in w), None)
        assert weather is not None
        assert weather["openmeteo"]["latitude"] == 51.5074
        assert weather["openmeteo"]["longitude"] == -0.1278
        assert weather["openmeteo"]["timezone"] == "Europe/London"
        assert weather["openmeteo"]["units"] == "imperial"
