from pathlib import Path
from unittest.mock import MagicMock, patch

from nexus.deploy.auth import generate_authelia_config


class TestGenerateAutheliaConfig:
    @patch("nexus.deploy.auth.SERVICES_PATH")
    def test_generate_authelia_config(
        self, mock_services_path: MagicMock, tmp_path: Path
    ):
        auth_dir = tmp_path / "auth"
        auth_dir.mkdir()

        sample_config = auth_dir / "configuration.yml.sample"
        sample_config.write_text(
            "domain: example.com\nsession:\n  domain: example.com\n"
        )

        mock_services_path.__truediv__.return_value = auth_dir

        generate_authelia_config("mydomain.com")

        target_config = auth_dir / "configuration.yml"
        assert target_config.exists()
        content = target_config.read_text()
        assert "mydomain.com" in content
        assert "example.com" not in content

    @patch("nexus.deploy.auth.SERVICES_PATH")
    def test_generate_authelia_config_dry_run(
        self, mock_services_path: MagicMock, tmp_path: Path
    ):
        auth_dir = tmp_path / "auth"
        auth_dir.mkdir()

        sample_config = auth_dir / "configuration.yml.sample"
        sample_config.write_text("domain: example.com\n")

        mock_services_path.__truediv__.return_value = auth_dir

        generate_authelia_config("mydomain.com", dry_run=True)

        target_config = auth_dir / "configuration.yml"
        assert not target_config.exists()

    @patch("nexus.deploy.auth.SERVICES_PATH")
    def test_generate_authelia_config_sample_not_found(
        self, mock_services_path: MagicMock, tmp_path: Path
    ):
        auth_dir = tmp_path / "auth"
        auth_dir.mkdir()

        mock_services_path.__truediv__.return_value = auth_dir

        generate_authelia_config("mydomain.com")
