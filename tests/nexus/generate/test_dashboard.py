from unittest.mock import patch

from nexus.generate.dashboard import (
    categorize_service,
    generate_dashboard_config,
    get_service_config,
    get_service_description,
    get_service_icon,
)


def test_get_service_description():
    assert get_service_description("traefik") == "Reverse proxy and SSL management"
    assert get_service_description("auth") == "SSO and 2FA authentication"
    assert get_service_description("dashboard") == "Homepage dashboard"
    assert get_service_description("backups") == "Automated backups"
    assert get_service_description("sure") == "Finance and budgeting"
    assert get_service_description("foundryvtt") == "Virtual Tabletop"
    assert get_service_description("jellyfin") == "Media server"
    assert get_service_description("transmission") == "Torrent client"
    assert get_service_description("unknown") == ""


def test_get_service_icon():
    assert get_service_icon("traefik") == "traefik.png"
    assert get_service_icon("auth") == "authelia.png"
    assert get_service_icon("dashboard") == "homepage.png"
    assert get_service_icon("backups") == "borg.png"
    assert get_service_icon("sure") == "sh-sure.png"
    assert get_service_icon("foundryvtt") == "foundryvtt.png"
    assert get_service_icon("jellyfin") == "jellyfin.png"
    assert get_service_icon("transmission") == "transmission.png"
    assert get_service_icon("unknown") == "unknown.png"


def test_categorize_service():
    assert categorize_service("traefik") == "Core"
    assert categorize_service("auth") == "Core"
    assert categorize_service("dashboard") == "Core"
    assert categorize_service("monitoring") == "Core"
    assert categorize_service("backups") == "Utilities"
    assert categorize_service("plex") == "Media"
    assert categorize_service("jellyfin") == "Media"
    assert categorize_service("transmission") == "Media"
    assert categorize_service("sure") == "Finance"
    assert categorize_service("foundryvtt") == "Gaming"
    assert categorize_service("nextcloud") == "Files"
    assert categorize_service("unknown") == "Other"


@patch("nexus.generate.dashboard.SERVICES_PATH")
def test_get_service_config_no_compose_file(mock_path, tmp_path):
    mock_path.__truediv__.return_value = tmp_path / "missing"

    result = get_service_config("missing")

    assert result == {}


@patch("nexus.generate.dashboard.SERVICES_PATH")
def test_get_service_config_with_list_labels(mock_path, tmp_path):
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

    def path_side_effect(arg):
        return tmp_path / arg

    mock_path.__truediv__.side_effect = path_side_effect

    result = get_service_config("plex")

    assert result["name"] == "plex"
    assert result["container"] == "plex"
    assert "plex.example.com" in result["rule"]


@patch("nexus.generate.dashboard.SERVICES_PATH")
def test_get_service_config_with_dict_labels(mock_path, tmp_path):
    service_dir = tmp_path / "jellyfin"
    service_dir.mkdir()
    compose_file = service_dir / "docker-compose.yml"
    compose_file.write_text("""
services:
  jellyfin:
    image: linuxserver/jellyfin
    labels:
      traefik.enable: "true"
      traefik.http.routers.jellyfin.rule: "Host(`jellyfin.example.com`)"
""")

    def path_side_effect(arg):
        return tmp_path / arg

    mock_path.__truediv__.side_effect = path_side_effect

    result = get_service_config("jellyfin")

    assert result["name"] == "jellyfin"
    assert "jellyfin.example.com" in result["rule"]


@patch("nexus.generate.dashboard.SERVICES_PATH")
def test_get_service_config_no_traefik_labels(mock_path, tmp_path):
    service_dir = tmp_path / "redis"
    service_dir.mkdir()
    compose_file = service_dir / "docker-compose.yml"
    compose_file.write_text("""
services:
  redis:
    image: redis:alpine
""")

    def path_side_effect(arg):
        return tmp_path / arg

    mock_path.__truediv__.side_effect = path_side_effect

    result = get_service_config("redis")

    assert result == {}


@patch("nexus.generate.dashboard.get_service_config")
def test_generate_dashboard_config(mock_get_config):
    mock_get_config.side_effect = [
        {
            "name": "plex",
            "container": "plex",
            "rule": "Host(`plex.example.com`)",
            "description": "Media streaming",
            "icon": "plex.png",
        },
        {
            "name": "jellyfin",
            "container": "jellyfin",
            "rule": "Host(`jellyfin.example.com`)",
            "description": "Media server",
            "icon": "jellyfin.png",
        },
    ]

    result = generate_dashboard_config(["plex", "jellyfin"], "example.com")

    assert "Media" in result
    assert len(result["Media"]) == 2


@patch("nexus.generate.dashboard.get_service_config")
def test_generate_dashboard_config_skips_dashboard(mock_get_config):
    result = generate_dashboard_config(["dashboard"], "example.com")

    mock_get_config.assert_not_called()
    assert result == {}


@patch("nexus.generate.dashboard.get_service_config")
def test_generate_dashboard_config_skips_empty(mock_get_config):
    mock_get_config.return_value = {}

    result = generate_dashboard_config(["missing"], "example.com")

    assert result == {}


@patch("nexus.generate.dashboard.get_service_config")
def test_generate_dashboard_config_fallback_url(mock_get_config):
    mock_get_config.return_value = {
        "name": "plex",
        "container": "plex",
        "rule": "PathPrefix(`/plex`)",
        "description": "Media streaming",
        "icon": "plex.png",
    }

    result = generate_dashboard_config(["plex"], "example.com")

    assert result["Media"][0]["plex"]["href"] == "https://plex.example.com"


@patch("nexus.generate.dashboard.get_service_config")
def test_generate_dashboard_config_dry_run(mock_get_config):
    mock_get_config.return_value = {
        "name": "plex",
        "container": "plex",
        "rule": "Host(`plex.example.com`)",
        "description": "Media streaming",
        "icon": "plex.png",
    }

    result = generate_dashboard_config(["plex"], "example.com", dry_run=True)

    assert "Media" in result
