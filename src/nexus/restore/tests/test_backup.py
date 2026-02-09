from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from nexus.restore.backup import list_backups, restore_backup, restore_database


class TestListBackups:
    @patch("nexus.restore.backup.run_command")
    def test_list_backups(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(
            stdout=(
                '[{"short_id": "abc123", "time": "2024-01-01T00:00:00Z", '
                '"paths": ["/userdata"]}, {"short_id": "def456", '
                '"time": "2024-01-02T00:00:00Z", "paths": ["/userdata"]}]'
            )
        )

        backups = list_backups()

        assert len(backups) == 2
        assert backups == ["abc123", "def456"]

    @patch("nexus.restore.backup.run_command")
    def test_list_backups_empty(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(stdout="[]")

        backups = list_backups()

        assert backups == []

    @patch("nexus.restore.backup.run_command")
    def test_list_backups_error(self, mock_run_command: MagicMock) -> None:
        mock_run_command.side_effect = Exception("Command failed")

        backups = list_backups()

        assert backups == []


class TestRestoreBackup:
    @patch("nexus.restore.backup.run_command")
    def test_restore_backup(self, mock_run_command: MagicMock) -> None:
        restore_backup("abc123")

        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert args == [
            "docker",
            "exec",
            "backrest",
            "restic",
            "restore",
            "abc123",
            "--target",
            "/tmp/restore",
        ]

    @patch("nexus.restore.backup.run_command")
    def test_restore_backup_with_services(self, mock_run_command: MagicMock) -> None:
        restore_backup("abc123", services=["plex", "jellyfin"])

        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert args == [
            "docker",
            "exec",
            "backrest",
            "restic",
            "restore",
            "abc123",
            "--target",
            "/tmp/restore",
            "--include",
            "/userdata/plex",
            "--include",
            "/userdata/jellyfin",
        ]

    def test_restore_backup_dry_run(self) -> None:
        restore_backup("abc123", dry_run=True)


class TestRestoreDatabase:
    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.ROOT_PATH")
    def test_restore_database_sure(
        self, mock_root_path: MagicMock, mock_run_command: MagicMock, tmp_path: Path
    ) -> None:
        sql_file = tmp_path / "sure.sql"
        sql_file.write_text("SELECT 1;")
        mock_root_path.return_value = tmp_path

        with patch("builtins.open", mock_open(read_data="SELECT 1;")):
            restore_database("sure", sql_file)

        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert "docker" in args
        assert "sure-db" in args

    def test_restore_database_dry_run(self, tmp_path: Path) -> None:
        sql_file = tmp_path / "sure.sql"
        sql_file.write_text("SELECT 1;")

        restore_database("sure", sql_file, dry_run=True)

    def test_restore_database_unsupported_service(self, tmp_path: Path) -> None:
        sql_file = tmp_path / "test.sql"
        sql_file.touch()

        with pytest.raises(NotImplementedError):
            restore_database("unsupported", sql_file)
