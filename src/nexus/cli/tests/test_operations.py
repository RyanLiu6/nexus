from unittest.mock import patch

from click.testing import CliRunner

from nexus.cli.operations import main


class TestMain:
    @patch("nexus.cli.operations.daily_tasks")
    def test_main_daily(self, mock_daily):
        runner = CliRunner()
        result = runner.invoke(main, ["--daily"])

        assert result.exit_code == 0
        mock_daily.assert_called_once()

    @patch("nexus.cli.operations.weekly_tasks")
    def test_main_weekly(self, mock_weekly):
        runner = CliRunner()
        result = runner.invoke(main, ["--weekly"])

        assert result.exit_code == 0
        mock_weekly.assert_called_once()

    @patch("nexus.cli.operations.monthly_tasks")
    def test_main_monthly(self, mock_monthly):
        runner = CliRunner()
        result = runner.invoke(main, ["--monthly"])

        assert result.exit_code == 0
        mock_monthly.assert_called_once()

    @patch("nexus.cli.operations.daily_tasks")
    @patch("nexus.cli.operations.weekly_tasks")
    @patch("nexus.cli.operations.monthly_tasks")
    def test_main_all(self, mock_monthly, mock_weekly, mock_daily):
        runner = CliRunner()
        result = runner.invoke(main, ["--all"])

        assert result.exit_code == 0
        mock_daily.assert_called_once()
        mock_weekly.assert_called_once()
        mock_monthly.assert_called_once()

    def test_main_no_args(self):
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
