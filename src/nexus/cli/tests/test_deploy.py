from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.deploy import _check_dependencies, _generate_configs, main


class TestCheckDependencies:
    def test_check_dependencies(self):
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/tool"
            missing = _check_dependencies()
            assert missing == []
            assert mock_which.call_count == 4

    def test_check_dependencies_missing_docker(self):
        def side_effect(cmd):
            if cmd == "docker":
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "docker" in missing

    def test_check_dependencies_missing_terraform(self):
        def side_effect(cmd):
            if cmd == "terraform":
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "terraform" in missing

    def test_check_dependencies_missing_ansible_vault(self):
        def side_effect(cmd):
            if cmd == "ansible-vault":
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "ansible-vault" in missing


class TestGenerateConfigs:
    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.generate_settings_config")
    @patch("nexus.cli.deploy.generate_bookmarks_config")
    @patch("nexus.cli.deploy.generate_widgets_config")
    def test_generate_configs(
        self,
        mock_widgets_config: MagicMock,
        mock_bookmarks_config: MagicMock,
        mock_settings_config: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_dashboard_config.return_value = {"services": []}
        mock_settings_config.return_value = {}
        mock_bookmarks_config.return_value = {}
        mock_widgets_config.return_value = {}

        _generate_configs(
            ["traefik", "tailscale-access"], "example.com", data_dir=str(tmp_path)
        )

        mock_dashboard_config.assert_called_once()

    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.generate_settings_config")
    @patch("nexus.cli.deploy.generate_bookmarks_config")
    @patch("nexus.cli.deploy.generate_widgets_config")
    def test_generate_configs_dry_run(
        self,
        mock_widgets_config: MagicMock,
        mock_bookmarks_config: MagicMock,
        mock_settings_config: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_dashboard_config.return_value = {"services": []}
        mock_settings_config.return_value = {}
        mock_bookmarks_config.return_value = {}
        mock_widgets_config.return_value = {}

        _generate_configs(
            ["traefik"], "example.com", data_dir=str(tmp_path), dry_run=True
        )

    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.generate_settings_config")
    @patch("nexus.cli.deploy.generate_bookmarks_config")
    @patch("nexus.cli.deploy.generate_widgets_config")
    def test_generate_configs_no_domain(
        self,
        mock_widgets_config: MagicMock,
        mock_bookmarks_config: MagicMock,
        mock_settings_config: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_dashboard_config.return_value = {"services": []}
        mock_settings_config.return_value = {}
        mock_bookmarks_config.return_value = {}
        mock_widgets_config.return_value = {}

        _generate_configs(["traefik"], None, data_dir=str(tmp_path))


class TestMain:
    def test_main(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.run_ansible") as mock_ansible,
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(
                main, ["--preset", "core", "--domain", "example.com", "-y"]
            )

            assert result.exit_code == 0, result.output
            mock_tf.assert_called_once()
            mock_ansible.assert_called_once()

    def test_main_with_all_services(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.run_ansible"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(main, ["--all", "--domain", "example.com", "-y"])

            assert result.exit_code == 0, result.output

    def test_main_default_preset(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.run_ansible"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(main, ["--domain", "example.com", "-y"])

            assert result.exit_code == 0, result.output

    def test_main_skip_dns(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.run_ansible"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--preset", "core", "--domain", "example.com", "--skip-dns", "-y"],
            )

            assert result.exit_code == 0, result.output
            mock_tf.assert_not_called()

    def test_main_skip_ansible(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.run_ansible") as mock_ansible,
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "--preset",
                    "core",
                    "--domain",
                    "example.com",
                    "--skip-ansible",
                    "-y",
                ],
            )

            assert result.exit_code == 0, result.output
            mock_ansible.assert_not_called()

    def test_main_dry_run(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.run_ansible"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["--preset", "core", "--domain", "example.com", "--dry-run", "-y"],
            )

            assert result.exit_code == 0, result.output

    def test_main_with_specific_services(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.run_ansible"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(
                main, ["traefik", "tailscale-access", "--domain", "example.com", "-y"]
            )

            assert result.exit_code == 0, result.output

    def test_main_missing_vault_exits(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = False
            mock_vault.parent = MagicMock()
            mock_vault.parent.__truediv__ = MagicMock(return_value=MagicMock())
            mock_vault.parent.__truediv__.return_value.exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(main, ["--preset", "core", "-y"])

            assert result.exit_code == 1

    def test_main_missing_tools_exits(self):
        with (
            patch(
                "nexus.cli.deploy._check_dependencies",
                return_value=["docker", "terraform"],
            ),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["--preset", "core", "-y"])

            assert result.exit_code == 1

    def test_main_creates_network_if_missing(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=False),
            patch("nexus.cli.deploy._create_docker_network") as mock_create,
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.run_ansible"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(
                main, ["--preset", "core", "--domain", "example.com", "-y"]
            )

            assert result.exit_code == 0, result.output
            mock_create.assert_called_once()

    def test_main_retrieves_r2_credentials_for_foundryvtt(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials") as mock_r2,
            patch("nexus.cli.deploy.run_ansible") as mock_ansible,
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            mock_r2.return_value = {
                "endpoint": "https://test.r2.cloudflarestorage.com",
                "access_key": "test_key",
                "secret_key": "test_secret",
                "bucket": "test-bucket",
            }

            runner = CliRunner()
            result = runner.invoke(
                main, ["foundryvtt", "--domain", "example.com", "-y"]
            )

            assert result.exit_code == 0, result.output
            mock_r2.assert_called_once()
            mock_ansible.assert_called_once()
            _args, kwargs = mock_ansible.call_args
            assert kwargs["r2_credentials"] == mock_r2.return_value

    def test_main_skips_r2_credentials_when_skip_dns(self):
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy._is_vault_encrypted", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.get_r2_credentials") as mock_r2,
            patch("nexus.cli.deploy.run_ansible") as mock_ansible,
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                main, ["foundryvtt", "--domain", "example.com", "--skip-dns", "-y"]
            )

            assert result.exit_code == 0, result.output
            mock_tf.assert_not_called()
            mock_r2.assert_not_called()
            mock_ansible.assert_called_once()
            _args, kwargs = mock_ansible.call_args
            assert kwargs["r2_credentials"] == {}
