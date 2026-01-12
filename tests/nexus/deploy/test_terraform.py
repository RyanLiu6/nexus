import json
from unittest.mock import MagicMock, patch

from nexus.deploy.terraform import get_public_ip, run_terraform


@patch("urllib.request.urlopen")
def test_get_public_ip(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = b"1.2.3.4"
    mock_response.__enter__.return_value = mock_response
    mock_urlopen.return_value = mock_response

    ip = get_public_ip()
    assert ip == "1.2.3.4"


@patch("urllib.request.urlopen")
def test_get_public_ip_fallback(mock_urlopen):
    mock_urlopen.side_effect = Exception("Network error")

    ip = get_public_ip()
    assert ip == "127.0.0.1"


@patch("nexus.deploy.terraform.run_command")
@patch("nexus.deploy.terraform.get_public_ip")
@patch("nexus.deploy.terraform.TERRAFORM_PATH")
def test_run_terraform(mock_tf_path, mock_get_ip, mock_run_command, tmp_path):
    mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
    (tmp_path / "main.tf").touch()

    tf_vars_path = tmp_path / "terraform.tfvars.json"

    def path_side_effect(arg):
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
@patch("nexus.deploy.terraform.get_public_ip")
@patch("nexus.deploy.terraform.TERRAFORM_PATH")
def test_run_terraform_dry_run(mock_tf_path, mock_get_ip, mock_run_command, tmp_path):
    mock_tf_path.__truediv__.return_value = tmp_path / "main.tf"
    (tmp_path / "main.tf").touch()
    mock_get_ip.return_value = "1.2.3.4"

    run_terraform(["plex"], "example.com", dry_run=True)

    mock_run_command.assert_not_called()
