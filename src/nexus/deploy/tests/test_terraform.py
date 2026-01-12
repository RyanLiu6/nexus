import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexus.deploy.terraform import _get_public_ip, run_terraform


class TestGetPublicIp:
    @patch("urllib.request.urlopen")
    def test_get_public_ip(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = b"1.2.3.4"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        ip = _get_public_ip()
        assert ip == "1.2.3.4"

    @patch("urllib.request.urlopen")
    def test_get_public_ip_fallback_on_error(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = Exception("Network error")

        ip = _get_public_ip()
        assert ip == "127.0.0.1"


class TestRunTerraform:
    @patch("nexus.deploy.terraform.run_command")
    @patch("nexus.deploy.terraform._get_public_ip")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform(
        self,
        mock_tf_path: MagicMock,
        mock_get_ip: MagicMock,
        mock_run_command: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
        (tmp_path / "main.tf").touch()

        tf_vars_path = tmp_path / "terraform.tfvars.json"

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_tf_path.__truediv__.side_effect = path_side_effect
        mock_tf_path.exists.return_value = True
        mock_get_ip.return_value = "10.0.0.1"

        services = ["plex", "sonarr"]
        run_terraform(services, "example.com", dry_run=False)

        assert tf_vars_path.exists()
        with open(tf_vars_path) as f:
            config = json.load(f)

        assert config["public_ip"] == "10.0.0.1"
        assert config["domain"] == "example.com"
        assert config["subdomains"] == ["plex", "sonarr"]
        assert config["proxied"] is False

        assert mock_run_command.call_count == 2
        args, _ = mock_run_command.call_args_list[1]
        assert args[0] == ["terraform", "apply", "-auto-approve"]

    @patch("nexus.deploy.terraform.run_command")
    @patch("nexus.deploy.terraform._get_public_ip")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_dry_run(
        self,
        mock_tf_path: MagicMock,
        mock_get_ip: MagicMock,
        mock_run_command: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
        (tmp_path / "main.tf").touch()
        mock_get_ip.return_value = "1.2.3.4"

        run_terraform(["plex"], "example.com", dry_run=True)

        mock_run_command.assert_not_called()

    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_no_config(self, mock_tf_path: MagicMock) -> None:
        # Simulate main.tf not existing
        mock_tf_path.__truediv__.return_value.exists.return_value = False

        run_terraform(["plex"], "example.com")

        # verifying logging or just that it returns without error
        # In this case just ensuring it runs without exception is enough given the code return early

    @patch("nexus.deploy.terraform.run_command")
    @patch("nexus.deploy.terraform._get_public_ip")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_error(
        self,
        mock_tf_path: MagicMock,
        mock_get_ip: MagicMock,
        mock_run_command: MagicMock,
        tmp_path: Path,
    ) -> None:
        import subprocess

        mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
        (tmp_path / "main.tf").touch()
        mock_get_ip.return_value = "1.2.3.4"

        # Simulate terraform command failure
        mock_run_command.side_effect = subprocess.CalledProcessError(1, "terraform")

        with pytest.raises(subprocess.CalledProcessError):
            run_terraform(["plex"], "example.com")
