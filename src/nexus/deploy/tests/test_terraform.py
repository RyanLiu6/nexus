import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexus.deploy.terraform import (
    _get_public_ip,
    _get_terraform_vars_from_vault,
    run_terraform,
)


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


class TestGetTerraformVarsFromVault:
    @patch("nexus.deploy.terraform.read_vault")
    def test_get_vars_tunnel_mode(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "cloudflare_api_token": "token123",
            "cloudflare_zone_id": "zone123",
            "cloudflare_account_id": "account123",
            "tunnel_secret": "secret123",
        }

        result = _get_terraform_vars_from_vault(use_tunnel=True)

        assert result["TF_VAR_cloudflare_api_token"] == "token123"
        assert result["TF_VAR_cloudflare_zone_id"] == "zone123"
        assert result["TF_VAR_cloudflare_account_id"] == "account123"
        assert result["TF_VAR_tunnel_secret"] == "secret123"

    @patch("nexus.deploy.terraform.read_vault")
    def test_get_vars_legacy_mode(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "cloudflare_api_token": "token123",
            "cloudflare_zone_id": "zone123",
            "cloudflare_account_id": "account123",
        }

        result = _get_terraform_vars_from_vault(use_tunnel=False)

        assert result["TF_VAR_cloudflare_api_token"] == "token123"
        assert "TF_VAR_tunnel_secret" not in result

    @patch("nexus.deploy.terraform.read_vault")
    def test_missing_vault_values(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "cloudflare_api_token": "CHANGE_ME",  # Unconfigured
            "cloudflare_zone_id": "zone123",
        }

        with pytest.raises(ValueError) as exc_info:
            _get_terraform_vars_from_vault(use_tunnel=False)

        assert "cloudflare_api_token" in str(exc_info.value)
        assert "cloudflare_account_id" in str(exc_info.value)

    @patch("nexus.deploy.terraform.read_vault")
    def test_vault_not_found(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.side_effect = FileNotFoundError("vault.yml not found")

        with pytest.raises(ValueError) as exc_info:
            _get_terraform_vars_from_vault(use_tunnel=True)

        assert "vault.yml not found" in str(exc_info.value)


class TestRunTerraform:
    @patch("nexus.deploy.terraform._run_terraform_cmd")
    @patch("nexus.deploy.terraform._get_public_ip")
    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_legacy_mode(
        self,
        mock_tf_path: MagicMock,
        mock_get_vault_vars: MagicMock,
        mock_get_ip: MagicMock,
        mock_run_cmd: MagicMock,
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
        mock_get_vault_vars.return_value = {
            "TF_VAR_cloudflare_api_token": "token",
            "TF_VAR_cloudflare_zone_id": "zone",
            "TF_VAR_cloudflare_account_id": "account",
        }

        services = ["plex", "sonarr"]
        run_terraform(services, "example.com", dry_run=False, use_tunnel=False)

        assert tf_vars_path.exists()
        with open(tf_vars_path) as f:
            config = json.load(f)

        assert config["public_ip"] == "10.0.0.1"
        assert config["domain"] == "example.com"
        assert config["subdomains"] == ["plex", "sonarr"]
        assert config["use_tunnel"] is False

        assert mock_run_cmd.call_count == 2

    @patch("nexus.deploy.terraform._run_terraform_cmd")
    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_tunnel_mode(
        self,
        mock_tf_path: MagicMock,
        mock_get_vault_vars: MagicMock,
        mock_run_cmd: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
        (tmp_path / "main.tf").touch()

        tf_vars_path = tmp_path / "terraform.tfvars.json"

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_tf_path.__truediv__.side_effect = path_side_effect
        mock_tf_path.exists.return_value = True
        mock_get_vault_vars.return_value = {
            "TF_VAR_cloudflare_api_token": "token",
            "TF_VAR_cloudflare_zone_id": "zone",
            "TF_VAR_cloudflare_account_id": "account",
            "TF_VAR_tunnel_secret": "secret",
        }

        run_terraform(["plex"], "example.com", dry_run=False, use_tunnel=True)

        assert tf_vars_path.exists()
        with open(tf_vars_path) as f:
            config = json.load(f)

        assert config["domain"] == "example.com"
        assert config["use_tunnel"] is True
        # Tunnel mode should not have public_ip or subdomains
        assert "public_ip" not in config
        assert "subdomains" not in config

    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_no_config(self, mock_tf_path: MagicMock) -> None:
        # Simulate main.tf not existing
        mock_tf_path.__truediv__.return_value.exists.return_value = False

        # Should return early without error
        run_terraform(["plex"], "example.com")

    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_missing_vault_values(
        self,
        mock_tf_path: MagicMock,
        mock_get_vault_vars: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
        (tmp_path / "main.tf").touch()

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_tf_path.__truediv__.side_effect = path_side_effect

        mock_get_vault_vars.side_effect = ValueError("Missing vault values")

        with pytest.raises(ValueError) as exc_info:
            run_terraform(["plex"], "example.com")

        assert "Missing vault values" in str(exc_info.value)

    @patch("nexus.deploy.terraform._run_terraform_cmd")
    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_error(
        self,
        mock_tf_path: MagicMock,
        mock_get_vault_vars: MagicMock,
        mock_run_cmd: MagicMock,
        tmp_path: Path,
    ) -> None:
        import subprocess

        mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
        (tmp_path / "main.tf").touch()

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_tf_path.__truediv__.side_effect = path_side_effect

        mock_get_vault_vars.return_value = {
            "TF_VAR_cloudflare_api_token": "token",
            "TF_VAR_cloudflare_zone_id": "zone",
            "TF_VAR_cloudflare_account_id": "account",
            "TF_VAR_tunnel_secret": "secret",
        }

        # Simulate terraform command failure
        mock_run_cmd.side_effect = subprocess.CalledProcessError(1, "terraform")

        with pytest.raises(subprocess.CalledProcessError):
            run_terraform(["plex"], "example.com")
