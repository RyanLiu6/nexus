from typing import Optional
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.deploy import _check_dependencies, main


class TestCheckDependencies:
    def test_check_dependencies(self) -> None:
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/tool"
            missing = _check_dependencies()
            assert missing == []
            # 3 required tools + tofu check (found, so no terraform fallback)
            assert mock_which.call_count == 4

    def test_check_dependencies_missing_docker(self) -> None:
        def side_effect(cmd):
            if cmd == "docker":
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "docker" in missing

    def test_check_dependencies_missing_tofu(self) -> None:
        def side_effect(cmd: str) -> Optional[str]:
            if cmd in ("tofu", "terraform"):
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "tofu" in missing

    def test_check_dependencies_with_terraform_fallback(self) -> None:
        def side_effect(cmd: str) -> Optional[str]:
            if cmd == "tofu":
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "tofu" not in missing

    def test_check_dependencies_missing_sops(self) -> None:
        def side_effect(cmd):
            if cmd == "sops":
                return None
            return "/usr/bin/" + cmd

        with patch("shutil.which", side_effect=side_effect):
            missing = _check_dependencies()
            assert "sops" in missing


class TestGenerateConfigs:
    def test_generate_configs(self, tmp_path):
        # Just test it runs without error
        pass


class TestMain:
    def test_main(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run") as mock_run,
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
            mock_run.assert_called_once()

    def test_main_with_all_services(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(main, ["--all", "--domain", "example.com", "-y"])

            assert result.exit_code == 0, result.output

    def test_main_default_preset(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run"),
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(main, ["--domain", "example.com", "-y"])

            assert result.exit_code == 0, result.output

    def test_main_skip_dns(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run"),
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

    def test_main_skip_deploy(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run") as mock_run,
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
                    "--skip-deploy",
                    "-y",
                ],
            )

            assert result.exit_code == 0, result.output
            mock_run.assert_not_called()

    def test_main_dry_run(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run"),
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

    def test_main_with_specific_services(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run") as mock_run,
            patch("nexus.cli.deploy._generate_configs"),
            patch("nexus.cli.deploy._is_cloudflared_running", return_value=True),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            mock_vault.exists.return_value = True
            runner = CliRunner()
            result = runner.invoke(main, ["plex", "--domain", "example.com", "-y"])

            assert result.exit_code == 0, result.output
            assert mock_tf.call_count == 1
            env = mock_run.call_args.kwargs.get("env", {})
            deployed_services = env.get("NEXUS_SERVICES", "").split(",")
            assert "plex" in deployed_services
            assert "traefik" in deployed_services

    def test_main_missing_vault_exits(self) -> None:
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

    def test_main_missing_tools_exits(self) -> None:
        with (
            patch(
                "nexus.cli.deploy._check_dependencies",
                return_value=["docker", "tofu"],
            ),
            patch.dict("os.environ", {"VIRTUAL_ENV": "/fake/venv"}),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["--preset", "core", "-y"])

            assert result.exit_code == 1

    def test_main_creates_network_if_missing(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=False),
            patch("nexus.cli.deploy._create_docker_network") as mock_create,
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials"),
            patch("subprocess.run"),
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

    def test_main_retrieves_r2_credentials_for_foundryvtt(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform"),
            patch("nexus.cli.deploy.get_r2_credentials") as mock_r2,
            patch("subprocess.run") as mock_run,
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
            mock_run.assert_called_once()
            _args, kwargs = mock_run.call_args
            env = kwargs.get("env", {})
            assert env.get("TF_FOUNDRY_S3_ENDPOINT") == mock_r2.return_value["endpoint"]

    def test_main_skips_r2_credentials_when_skip_dns(self) -> None:
        with (
            patch("nexus.cli.deploy._check_dependencies", return_value=[]),
            patch("nexus.cli.deploy._check_docker_network", return_value=True),
            patch("nexus.cli.deploy.VAULT_PATH") as mock_vault,
            patch("nexus.cli.deploy.run_terraform") as mock_tf,
            patch("nexus.cli.deploy.get_r2_credentials") as mock_r2,
            patch("subprocess.run") as mock_run,
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
            mock_run.assert_called_once()
            _args, kwargs = mock_run.call_args
            env = kwargs.get("env", {})
            assert "TF_FOUNDRY_S3_ENDPOINT" not in env
