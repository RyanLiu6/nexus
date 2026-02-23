from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.restore import _verify_backup, main


class TestVerifyBackup:
    @patch("nexus.cli.restore.run_command")
    def test_verify_backup_valid(self, mock_run_command: MagicMock) -> None:
        result = _verify_backup()

        assert result is True
        mock_run_command.assert_called_once()

    @patch("nexus.cli.restore.run_command")
    def test_verify_backup_invalid(self, mock_run_command: MagicMock) -> None:
        mock_run_command.side_effect = Exception("Check failed")

        result = _verify_backup()

        assert result is False


class TestMain:
    @patch("nexus.cli.restore.list_backups")
    def test_main_list_backups(self, mock_list: MagicMock) -> None:
        mock_list.return_value = ["abc123", "def456"]

        runner = CliRunner()
        result = runner.invoke(main, ["--list"])

        assert result.exit_code == 0
        assert "abc123" in result.output
        assert "def456" in result.output

    @patch("nexus.cli.restore.list_backups")
    def test_main_list_no_backups(self, mock_list: MagicMock) -> None:
        mock_list.return_value = []

        runner = CliRunner()
        result = runner.invoke(main, ["--list"])

        assert result.exit_code == 0
        mock_list.assert_called_once()

    @patch("nexus.cli.restore.restore_backup")
    def test_main_restore(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--snapshot", "abc123"])

        assert result.exit_code == 0
        mock_restore.assert_called_once()

    @patch("nexus.cli.restore.list_backups")
    def test_main_restore_no_snapshot(self, mock_list: MagicMock) -> None:
        mock_list.return_value = []

        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0

    @patch("nexus.cli.restore.run_command")
    def test_main_verify(self, mock_run_command: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--verify"])

        assert result.exit_code == 0
        mock_run_command.assert_called_once()

    @patch("nexus.cli.restore.restore_backup")
    def test_main_restore_with_service(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--snapshot", "abc123", "--service", "plex"])

        assert result.exit_code == 0
        mock_restore.assert_called_once()

    @patch("nexus.cli.restore.restore_database")
    def test_main_restore_database(
        self, mock_db_restore: MagicMock, tmp_path: Path
    ) -> None:
        sql_file = tmp_path / "sure.sql"
        sql_file.touch()

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--snapshot",
                "abc123",
                "--db",
                str(sql_file),
                "--service",
                "sure",
            ],
        )

        assert result.exit_code == 0
        mock_db_restore.assert_called_once()

    def test_main_restore_database_no_service(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--snapshot", "abc123", "--db", "/tmp/db.sql"])

        assert result.exit_code == 0

    def test_main_restore_database_file_not_found(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--snapshot",
                "abc123",
                "--db",
                "/nonexistent.sql",
                "--service",
                "sure",
            ],
        )

        assert result.exit_code == 0

    @patch("nexus.cli.restore.restore_backup")
    def test_main_restore_dry_run(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--snapshot", "abc123", "--dry-run"])

        assert result.exit_code == 0

    @patch("nexus.cli.restore.restore_backup")
    @patch("nexus.cli.restore.list_backups")
    def test_main_interactive_restore(
        self, mock_list: MagicMock, mock_restore: MagicMock
    ) -> None:
        mock_list.return_value = ["abc123", "def456"]

        runner = CliRunner()
        result = runner.invoke(main, [], input="1\n")

        assert result.exit_code == 0
        assert "abc123" in result.output
        assert "def456" in result.output
        mock_restore.assert_called_once()
        args = mock_restore.call_args[0]
        assert args[0] == "abc123"
