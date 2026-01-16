from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.health import main


class TestMain:
    @patch("nexus.cli.health.check_docker_containers")
    @patch("nexus.cli.health.check_disk_space")
    @patch("nexus.cli.health.check_ssl_certificates")
    @patch("nexus.cli.health.check_all_services")
    def test_main_all_healthy(
        self,
        mock_check_all: MagicMock,
        mock_ssl: MagicMock,
        mock_disk: MagicMock,
        mock_docker: MagicMock,
    ):
        mock_docker.return_value = {"traefik": True, "auth": True}
        mock_disk.return_value = {
            "total": "100G",
            "used": "50G",
            "available": "50G",
            "usage_percent": "50%",
        }
        mock_ssl.return_value = {"traefik": True, "grafana": True}

        async def mock_check(services):
            for svc in services:
                svc.healthy = True

        mock_check_all.side_effect = mock_check

        runner = CliRunner()
        result = runner.invoke(main, ["--domain", "example.com"])

        assert result.exit_code == 0
        assert "Health Check Report" in result.output

    @patch("nexus.cli.health.check_docker_containers")
    @patch("nexus.cli.health.check_disk_space")
    @patch("nexus.cli.health.check_ssl_certificates")
    @patch("nexus.cli.health.check_all_services")
    def test_main_unhealthy_service(
        self,
        mock_check_all: MagicMock,
        mock_ssl: MagicMock,
        mock_disk: MagicMock,
        mock_docker: MagicMock,
    ):
        mock_docker.return_value = {"traefik": False}
        mock_disk.return_value = {}
        mock_ssl.return_value = {}

        async def mock_check(services):
            for svc in services:
                svc.healthy = False
                svc.error = "Connection refused"

        mock_check_all.side_effect = mock_check

        runner = CliRunner()
        result = runner.invoke(main, ["--domain", "example.com"])

        assert result.exit_code == 1

    @patch("nexus.cli.health.check_docker_containers")
    @patch("nexus.cli.health.check_disk_space")
    @patch("nexus.cli.health.check_all_services")
    def test_main_no_domain(
        self,
        mock_check_all: MagicMock,
        mock_disk: MagicMock,
        mock_docker: MagicMock,
    ):
        mock_docker.return_value = {}
        mock_disk.return_value = {}

        async def mock_check(services):
            for svc in services:
                svc.healthy = True

        mock_check_all.side_effect = mock_check

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0

    @patch("nexus.cli.health.check_docker_containers")
    @patch("nexus.cli.health.check_disk_space")
    @patch("nexus.cli.health.check_all_services")
    def test_main_critical_only(
        self,
        mock_check_all: MagicMock,
        mock_disk: MagicMock,
        mock_docker: MagicMock,
    ):
        mock_docker.return_value = {}
        mock_disk.return_value = {}

        async def mock_check(services):
            for svc in services:
                svc.healthy = True

        mock_check_all.side_effect = mock_check

        runner = CliRunner()
        result = runner.invoke(main, ["--critical-only"])

        assert result.exit_code == 0

    @patch("nexus.cli.health.check_docker_containers")
    @patch("nexus.cli.health.check_disk_space")
    @patch("nexus.cli.health.check_all_services")
    def test_main_verbose(
        self,
        mock_check_all: MagicMock,
        mock_disk: MagicMock,
        mock_docker: MagicMock,
    ):
        mock_docker.return_value = {}
        mock_disk.return_value = {}

        async def mock_check(services):
            for svc in services:
                svc.healthy = True

        mock_check_all.side_effect = mock_check

        runner = CliRunner()
        result = runner.invoke(main, ["--verbose"])

        assert result.exit_code == 0

    @patch("nexus.cli.health.check_docker_containers")
    @patch("nexus.cli.health.check_disk_space")
    @patch("nexus.cli.health.check_all_services")
    def test_main_with_alert_webhook(
        self,
        mock_check_all: MagicMock,
        mock_disk: MagicMock,
        mock_docker: MagicMock,
    ):
        mock_docker.return_value = {}
        mock_disk.return_value = {}

        async def mock_check(services):
            for svc in services:
                svc.healthy = False

        mock_check_all.side_effect = mock_check

        runner = CliRunner()
        result = runner.invoke(main, ["--alert-webhook", "https://webhook.url"])

        assert result.exit_code == 1
