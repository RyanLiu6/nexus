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
    @patch("nexus.cli.deploy.SERVICES_PATH")
    def test_generate_configs(
        self,
        mock_services_path: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_dashboard_config.return_value = {"services": []}
        dashboard_dir = tmp_path / "dashboard" / "config"
        dashboard_dir.mkdir(parents=True)
        mock_services_path.__truediv__.return_value = dashboard_dir.parent

        _generate_configs(["traefik", "tailscale-access"], "example.com")

        mock_dashboard_config.assert_called_once()

    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.SERVICES_PATH")
    def test_generate_configs_dry_run(
        self,
        mock_services_path: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_dashboard_config.return_value = {"services": []}

        _generate_configs(["traefik"], "example.com", dry_run=True)

    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.SERVICES_PATH")
    def test_generate_configs_no_domain(
        self,
        mock_services_path: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_dashboard_config.return_value = {"services": []}
        dashboard_dir = tmp_path / "dashboard" / "config"
        dashboard_dir.mkdir(parents=True)
        mock_services_path.__truediv__.return_value = dashboard_dir.parent

        _generate_configs(["traefik"], None)


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
