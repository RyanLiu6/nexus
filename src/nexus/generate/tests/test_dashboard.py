from pathlib import Path
from unittest.mock import MagicMock, patch

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
    def test_get_service_description(self) -> None:
        assert get_service_description("traefik") == "Reverse proxy and SSL management"
        assert get_service_description("tailscale-access") == "Auth Middleware"
        assert get_service_description("dashboard") == "Homepage dashboard"
        assert get_service_description("backups") == "Automated backups"
        assert get_service_description("sure") == "Finance and budgeting"
        assert get_service_description("sure-web") == "Finance and budgeting"
        assert get_service_description("foundryvtt") == "Virtual Tabletop"
        assert get_service_description("jellyfin") == "Media server"
        assert get_service_description("transmission") == "Torrent client"

    def test_get_service_description_unknown(self) -> None:
        assert get_service_description("unknown") == ""


class TestGetServiceIcon:
    def test_get_service_icon(self) -> None:
        assert get_service_icon("traefik") == "si-traefik"
        assert get_service_icon("tailscale-access") == "si-tailscale"
        assert get_service_icon("dashboard") == "si-homeassistant"
        assert get_service_icon("backups") == "mdi-backup-restore"
        assert get_service_icon("sure") == "mdi-chart-line"
        assert get_service_icon("sure-web") == "mdi-chart-line"
        assert get_service_icon("foundryvtt") == "si-foundryvirtualtabletop"
        assert get_service_icon("jellyfin") == "si-jellyfin"
        assert get_service_icon("transmission") == "si-transmission"
        assert get_service_icon("prometheus") == "si-prometheus"
        assert get_service_icon("grafana") == "si-grafana"
        assert get_service_icon("alertmanager") == "mdi-alert"

    def test_get_service_icon_unknown(self) -> None:
        assert get_service_icon("unknown") == "unknown.png"


class TestCategorizeService:
    def test_categorize_service(self) -> None:
        assert categorize_service("traefik") == "Core"
        assert categorize_service("tailscale-access") == "Core"
        assert categorize_service("dashboard") == "Core"
        assert categorize_service("monitoring") == "Core"
        assert categorize_service("prometheus") == "Core"
        assert categorize_service("grafana") == "Core"
        assert categorize_service("alertmanager") == "Core"
        assert categorize_service("backups") == "Utilities"
        assert categorize_service("plex") == "Media"
        assert categorize_service("jellyfin") == "Media"
        assert categorize_service("transmission") == "Media"
        assert categorize_service("sure") == "Finance"
        assert categorize_service("sure-web") == "Finance"
        assert categorize_service("foundryvtt") == "Gaming"
        assert categorize_service("nextcloud") == "Files"

    def test_categorize_service_unknown(self) -> None:
        assert categorize_service("unknown") == "Other"


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

        # Result is list[dict[category, list[service]]]
        # We need to find the "Media" category item in the list
        media_category = next((item for item in result if "Media" in item), None)
        assert media_category is not None
        assert len(media_category["Media"]) == 2

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_skips_dashboard(
        self, mock_get_config: MagicMock
    ) -> None:
        result = generate_dashboard_config(["dashboard"], "example.com")

        mock_get_config.assert_not_called()
        assert result == []

    @patch("nexus.generate.dashboard.get_service_config")
    def test_generate_dashboard_config_skips_empty(
        self, mock_get_config: MagicMock
    ) -> None:
        mock_get_config.return_value = []

        result = generate_dashboard_config(["missing"], "example.com")

        assert result == []

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

        gaming_category = next((item for item in result if "Gaming" in item), None)
        assert gaming_category is not None
        href = gaming_category["Gaming"][0]["foundryvtt"]["href"]
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
        assert config["hideVersion"] is True


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
        assert len(config) == 5

        widget_types = [next(iter(w.keys())) for w in config]
        assert "greeting" in widget_types
        assert "datetime" in widget_types
        assert "openmeteo" in widget_types
        assert "resources" in widget_types
        assert "search" in widget_types

        search = next((w for w in config if "search" in w), None)
        assert search is not None
        assert search["search"]["provider"] == "google"

        resources = next((w for w in config if "resources" in w), None)
        assert resources is not None
        assert resources["resources"]["cpu"] is True
        assert resources["resources"]["memory"] is True
        assert resources["resources"]["disk"] == "/"

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
