from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.backup import main


class TestMain:
    @patch("nexus.cli.backup.push_backup")
    def test_main_push_local(self, mock_push: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--target", "local"])

        assert result.exit_code == 0
        mock_push.assert_called_once_with(target="local", dry_run=False)

    @patch("nexus.cli.backup.push_backup")
    def test_main_push_all(self, mock_push: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        mock_push.assert_called_once_with(target="all", dry_run=False)

    @patch("nexus.cli.backup.push_backup")
    def test_main_push_dry_run(self, mock_push: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--dry-run"])

        assert result.exit_code == 0
        mock_push.assert_called_once_with(target="all", dry_run=True)

    @patch("nexus.cli.backup.push_backup")
    def test_main_push_r2(self, mock_push: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--target", "r2"])

        assert result.exit_code == 0
        mock_push.assert_called_once_with(target="r2", dry_run=False)

    @patch("nexus.cli.backup.push_backup")
    def test_main_push_error(self, mock_push: MagicMock) -> None:
        mock_push.side_effect = RuntimeError("Backup failed")

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 1
