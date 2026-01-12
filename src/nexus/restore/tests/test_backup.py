from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from nexus.restore.backup import list_backups, restore_backup, restore_database


class TestListBackups:
    @patch("nexus.restore.backup.BACKUP_DIR")
    def test_list_backups(self, mock_backup_dir: MagicMock, tmp_path: Path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        (backup_dir / "backup-2024-01-01.tar.gz").touch()
        (backup_dir / "backup-2024-01-02.tar.gz").touch()
        (backup_dir / "backup-2024-01-03.tar.gz").touch()

        mock_backup_dir.exists.return_value = True
        mock_backup_dir.glob.return_value = list(backup_dir.glob("*.tar.gz"))

        backups = list_backups()

        assert len(backups) == 3

    @patch("nexus.restore.backup.BACKUP_DIR")
    def test_list_backups_empty(self, mock_backup_dir: MagicMock, tmp_path: Path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        mock_backup_dir.exists.return_value = True
        mock_backup_dir.glob.return_value = []

        backups = list_backups()

        assert backups == []

    @patch("nexus.restore.backup.BACKUP_DIR")
    def test_list_backups_dir_not_exists(self, mock_backup_dir: MagicMock):
        mock_backup_dir.exists.return_value = False

        backups = list_backups()

        assert backups == []


class TestRestoreBackup:
    @patch("nexus.restore.backup.run_command")
    def test_restore_backup(self, mock_run_command: MagicMock, tmp_path: Path):
        backup_file = tmp_path / "backup.tar.gz"
        backup_file.touch()

        restore_backup(backup_file)

        assert mock_run_command.call_count == 3
        calls = mock_run_command.call_args_list

        assert calls[0][0][0] == ["docker", "compose", "down"]
        assert calls[1][0][0] == ["tar", "-xzf", str(backup_file), "-C", "/"]
        assert calls[2][0][0] == ["docker", "compose", "up", "-d"]

    @patch("nexus.restore.backup.run_command")
    def test_restore_backup_with_services(
        self, mock_run_command: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "backup.tar.gz"
        backup_file.touch()

        restore_backup(backup_file, services=["plex", "jellyfin"])

        assert mock_run_command.call_count == 3

    def test_restore_backup_dry_run(self, tmp_path: Path):
        backup_file = tmp_path / "backup.tar.gz"
        backup_file.touch()

        restore_backup(backup_file, dry_run=True)


class TestRestoreDatabase:
    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.ROOT_PATH")
    def test_restore_database_sure(
        self, mock_root_path: MagicMock, mock_run_command: MagicMock, tmp_path: Path
    ):
        sql_file = tmp_path / "sure.sql"
        sql_file.write_text("SELECT 1;")
        mock_root_path.return_value = tmp_path

        with patch("builtins.open", mock_open(read_data="SELECT 1;")):
            restore_database("sure", sql_file)

        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert "docker" in args
        assert "sure-db" in args

    def test_restore_database_dry_run(self, tmp_path: Path):
        sql_file = tmp_path / "sure.sql"
        sql_file.write_text("SELECT 1;")

        restore_database("sure", sql_file, dry_run=True)

    def test_restore_database_unsupported_service(self, tmp_path: Path):
        sql_file = tmp_path / "test.sql"
        sql_file.touch()

        with pytest.raises(NotImplementedError):
            restore_database("unsupported", sql_file)
