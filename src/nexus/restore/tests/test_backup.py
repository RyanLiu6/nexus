import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from nexus.restore.backup import (
    get_backrest_config,
    list_backups,
    push_backup,
    restore_backup,
    restore_database,
)

SAMPLE_CONFIG = {
    "repos": [
        {"id": "local", "uri": "/repos"},
        {"id": "r2", "uri": "rclone:r2:my-bucket"},
    ],
    "plans": [
        {
            "id": "daily-local",
            "repo": "local",
            "retention": {"policyKeepLastN": 3},
        },
        {
            "id": "daily-r2",
            "repo": "r2",
            "retention": {"policyKeepLastN": 1},
        },
    ],
}


class TestGetBackrestConfig:
    @patch("nexus.restore.backup.run_command")
    def test_get_backrest_config(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(stdout=json.dumps(SAMPLE_CONFIG))

        config = get_backrest_config()

        assert config == SAMPLE_CONFIG
        mock_run_command.assert_called_once_with(
            ["docker", "exec", "backrest", "cat", "/config/config.json"]
        )

    @patch("nexus.restore.backup.run_command")
    def test_get_backrest_config_error(self, mock_run_command: MagicMock) -> None:
        mock_run_command.side_effect = Exception("Container not running")

        with pytest.raises(RuntimeError, match="Failed to read Backrest config"):
            get_backrest_config()


class TestPushBackup:
    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    def test_push_backup(
        self, mock_config: MagicMock, mock_run_command: MagicMock
    ) -> None:
        mock_config.return_value = SAMPLE_CONFIG

        push_backup(target="local")

        calls = mock_run_command.call_args_list
        assert len(calls) == 2
        backup_cmd = calls[0][0][0]
        forget_cmd = calls[1][0][0]
        assert backup_cmd == [
            "docker",
            "exec",
            "backrest",
            "restic",
            "-r",
            "/repos",
            "backup",
            "/userdata",
        ]
        assert forget_cmd == [
            "docker",
            "exec",
            "backrest",
            "restic",
            "-r",
            "/repos",
            "forget",
            "--keep-last",
            "3",
            "--prune",
        ]

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    def test_push_backup_r2(
        self, mock_config: MagicMock, mock_run_command: MagicMock
    ) -> None:
        mock_config.return_value = SAMPLE_CONFIG

        push_backup(target="r2")

        calls = mock_run_command.call_args_list
        assert len(calls) == 2
        backup_cmd = calls[0][0][0]
        forget_cmd = calls[1][0][0]
        assert backup_cmd == [
            "docker",
            "exec",
            "backrest",
            "restic",
            "-r",
            "rclone:r2:my-bucket",
            "backup",
            "/userdata",
        ]
        assert forget_cmd == [
            "docker",
            "exec",
            "backrest",
            "restic",
            "-r",
            "rclone:r2:my-bucket",
            "forget",
            "--keep-last",
            "1",
            "--prune",
        ]

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    def test_push_backup_all(
        self, mock_config: MagicMock, mock_run_command: MagicMock
    ) -> None:
        mock_config.return_value = SAMPLE_CONFIG

        push_backup(target="all")

        assert mock_run_command.call_count == 4
        uris = [c[0][0][5] for c in mock_run_command.call_args_list]
        assert "/repos" in uris
        assert "rclone:r2:my-bucket" in uris

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    def test_push_backup_dry_run(
        self, mock_config: MagicMock, mock_run_command: MagicMock
    ) -> None:
        mock_config.return_value = SAMPLE_CONFIG

        push_backup(target="all", dry_run=True)

        mock_run_command.assert_not_called()

    def test_push_backup_invalid_target(self) -> None:
        with pytest.raises(ValueError, match="Invalid target"):
            push_backup(target="invalid")


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
            "-r",
            "/repos",
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
            "-r",
            "/repos",
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
