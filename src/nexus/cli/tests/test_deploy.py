import subprocess
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from nexus.cli.deploy import _check_dependencies, _generate_configs, main


class TestCheckDependencies:
    def test_check_dependencies_all_present(self):
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/tool"
            _check_dependencies()
            assert mock_which.call_count == 3

    def test_check_dependencies_missing_docker(self):
        def side_effect(cmd):
            if cmd == "docker":
                return None
            return "/usr/bin/" + cmd

        with (
            patch("shutil.which", side_effect=side_effect),
            pytest.raises(SystemExit),
        ):
            _check_dependencies()

    def test_check_dependencies_missing_terraform(self):
        def side_effect(cmd):
            if cmd == "terraform":
                return None
            return "/usr/bin/" + cmd

        with (
            patch("shutil.which", side_effect=side_effect),
            pytest.raises(SystemExit),
        ):
            _check_dependencies()

    def test_check_dependencies_missing_ansible(self):
        def side_effect(cmd):
            if cmd == "ansible":
                return None
            return "/usr/bin/" + cmd

        with (
            patch("shutil.which", side_effect=side_effect),
            pytest.raises(SystemExit),
        ):
            _check_dependencies()


class TestGenerateConfigs:
    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.generate_authelia_config")
    @patch("nexus.cli.deploy.SERVICES_PATH")
    def test_generate_configs(
        self,
        mock_services_path: MagicMock,
        mock_auth_config: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path,
    ):
        mock_dashboard_config.return_value = {"services": []}
        dashboard_dir = tmp_path / "dashboard" / "config"
        dashboard_dir.mkdir(parents=True)
        mock_services_path.__truediv__.return_value = dashboard_dir.parent

        _generate_configs(["traefik", "auth"], "example.com")

        mock_dashboard_config.assert_called_once()
        mock_auth_config.assert_called_once_with("example.com", False)

    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.SERVICES_PATH")
    def test_generate_configs_dry_run(
        self,
        mock_services_path: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path,
    ):
        mock_dashboard_config.return_value = {"services": []}

        _generate_configs(["traefik"], "example.com", dry_run=True)

    @patch("nexus.cli.deploy.generate_dashboard_config")
    @patch("nexus.cli.deploy.SERVICES_PATH")
    def test_generate_configs_no_domain(
        self,
        mock_services_path: MagicMock,
        mock_dashboard_config: MagicMock,
        tmp_path,
    ):
        mock_dashboard_config.return_value = {"services": []}
        dashboard_dir = tmp_path / "dashboard" / "config"
        dashboard_dir.mkdir(parents=True)
        mock_services_path.__truediv__.return_value = dashboard_dir.parent

        _generate_configs(["traefik"], None)


class TestMain:
    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_with_preset(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["--preset", "core", "--domain", "example.com"])

        assert result.exit_code == 0
        mock_terraform.assert_called_once()
        mock_ansible.assert_called_once()

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_with_all_services(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["--all", "--domain", "example.com"])

        assert result.exit_code == 0

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_no_services(self, mock_generate: MagicMock, mock_deps: MagicMock):
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_skip_dns(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(
            main, ["--preset", "core", "--domain", "example.com", "--skip-dns"]
        )

        assert result.exit_code == 0
        mock_terraform.assert_not_called()

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_skip_ansible(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(
            main, ["--preset", "core", "--domain", "example.com", "--skip-ansible"]
        )

        assert result.exit_code == 0
        mock_ansible.assert_not_called()

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_dry_run(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(
            main, ["--preset", "core", "--domain", "example.com", "--dry-run"]
        )

        assert result.exit_code == 0

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_with_specific_services(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["traefik", "auth", "--domain", "example.com"])

        assert result.exit_code == 0

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy.run_terraform")
    @patch("nexus.cli.deploy.run_ansible")
    @patch("nexus.cli.deploy._generate_configs")
    def test_main_verbose(
        self,
        mock_generate: MagicMock,
        mock_ansible: MagicMock,
        mock_terraform: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()
        result = runner.invoke(
            main, ["--preset", "core", "--domain", "example.com", "--verbose"]
        )

        assert result.exit_code == 0

    @patch("nexus.cli.deploy._check_dependencies")
    @patch("nexus.cli.deploy._generate_configs")
    @patch.dict("os.environ", {"NEXUS_DOMAIN": "env.example.com"})
    def test_main_domain_from_env(
        self,
        mock_generate: MagicMock,
        mock_deps: MagicMock,
    ):
        runner = CliRunner()

        with (
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.run_ansible"),
        ):
            runner.invoke(main, ["--preset", "core"])

            if mock_tf.called:
                args = mock_tf.call_args
                assert "env.example.com" in str(args)
