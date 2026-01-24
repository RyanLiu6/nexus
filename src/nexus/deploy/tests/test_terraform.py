import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexus.deploy.terraform import (
    _get_terraform_vars_from_vault,
    get_gateway_dns_ips,
    run_terraform,
)


class TestGetTerraformVarsFromVault:
    @patch("nexus.deploy.terraform.read_vault")
    def test_get_terraform_vars_from_vault(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "cloudflare_api_token": "token123",
            "cloudflare_zone_id": "zone123",
            "cloudflare_account_id": "account123",
            "tunnel_secret": "secret123",
        }

        result = _get_terraform_vars_from_vault()

        assert result["TF_VAR_cloudflare_api_token"] == "token123"
        assert result["TF_VAR_cloudflare_zone_id"] == "zone123"
        assert result["TF_VAR_cloudflare_account_id"] == "account123"
        assert result["TF_VAR_tunnel_secret"] == "secret123"

    @patch("nexus.deploy.terraform.read_vault")
    def test_with_tailscale_api_key(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "cloudflare_api_token": "token123",
            "cloudflare_zone_id": "zone123",
            "cloudflare_account_id": "account123",
            "tunnel_secret": "secret123",
            "tailscale_api_key": "tskey-api-123",
        }

        result = _get_terraform_vars_from_vault()

        assert result["TF_VAR_tailscale_api_key"] == "tskey-api-123"

    @patch("nexus.deploy.terraform.read_vault")
    def test_missing_vault_values(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "cloudflare_api_token": "CHANGE_ME",  # Unconfigured
            "cloudflare_zone_id": "zone123",
        }

        with pytest.raises(ValueError) as exc_info:
            _get_terraform_vars_from_vault()

        assert "cloudflare_api_token" in str(exc_info.value)
        assert "cloudflare_account_id" in str(exc_info.value)

    @patch("nexus.deploy.terraform.read_vault")
    def test_vault_not_found(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.side_effect = FileNotFoundError("vault.yml not found")

        with pytest.raises(ValueError) as exc_info:
            _get_terraform_vars_from_vault()

        assert "vault.yml not found" in str(exc_info.value)


class TestRunTerraform:
    @patch("nexus.deploy.terraform._run_terraform_cmd")
    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform(
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

        run_terraform(["plex"], "example.com", dry_run=False)

        assert tf_vars_path.exists()
        with open(tf_vars_path) as f:
            config = json.load(f)

        assert config["domain"] == "example.com"
        assert "subdomains" in config
        assert mock_run_cmd.call_count == 2

    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_no_config(self, mock_tf_path: MagicMock) -> None:
        mock_tf_path.__truediv__.return_value.exists.return_value = False

        run_terraform(["plex"], "example.com")

    @patch("nexus.deploy.terraform._run_terraform_cmd")
    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.read_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_with_tailscale_users(
        self,
        mock_tf_path: MagicMock,
        mock_read_vault: MagicMock,
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
        mock_read_vault.return_value = {
            "tailscale_users": {
                "admins": ["admin@example.com"],
                "members": ["user@example.com"],
            },
            "tailnet_id": "tail1234",
            "tailscale_server_ip": "100.64.0.1",
        }

        run_terraform(["plex"], "example.com", dry_run=False)

        assert tf_vars_path.exists()
        with open(tf_vars_path) as f:
            config = json.load(f)

        assert config["tailscale_users"] == {
            "admins": ["admin@example.com"],
            "members": ["user@example.com"],
        }
        assert config["tailnet_id"] == "tail1234"
        assert config["tailscale_server_ip"] == "100.64.0.1"

    @patch("nexus.deploy.terraform._run_terraform_cmd")
    @patch("nexus.deploy.terraform._get_terraform_vars_from_vault")
    @patch("nexus.deploy.terraform.read_vault")
    @patch("nexus.deploy.terraform.TERRAFORM_PATH")
    def test_run_terraform_without_tailscale_config(
        self,
        mock_tf_path: MagicMock,
        mock_read_vault: MagicMock,
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
        mock_read_vault.side_effect = FileNotFoundError("vault not found")

        run_terraform(["plex"], "example.com", dry_run=False)

        assert tf_vars_path.exists()
        with open(tf_vars_path) as f:
            config = json.load(f)

        assert config["tailscale_users"] == {}
        assert config["tailnet_id"] == ""
        assert config["tailscale_server_ip"] == ""

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

        mock_run_cmd.side_effect = subprocess.CalledProcessError(1, "terraform")

        with pytest.raises(subprocess.CalledProcessError):
            run_terraform(["plex"], "example.com")


class TestGetGatewayDnsIps:
    @patch("subprocess.run")
    def test_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value.stdout = json.dumps(
            {
                "gateway_ipv4_primary": {"value": "1.2.3.4"},
                "gateway_ipv4_backup": {"value": "5.6.7.8"},
            }
        )
        mock_run.return_value.returncode = 0

        primary, backup = get_gateway_dns_ips()

        assert primary == "1.2.3.4"
        assert backup == "5.6.7.8"

    @patch("subprocess.run")
    def test_subprocess_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.CalledProcessError(1, "terraform")

        primary, backup = get_gateway_dns_ips()

        assert primary == ""
        assert backup == ""

    @patch("subprocess.run")
    def test_json_error(self, mock_run: MagicMock) -> None:
        mock_run.return_value.stdout = "invalid json"
        mock_run.return_value.returncode = 0

        primary, backup = get_gateway_dns_ips()

        assert primary == ""
        assert backup == ""

    @patch("subprocess.run")
    def test_missing_keys(self, mock_run: MagicMock) -> None:
        mock_run.return_value.stdout = "{}"
        mock_run.return_value.returncode = 0

        primary, backup = get_gateway_dns_ips()

        assert primary == ""
        assert backup == ""
