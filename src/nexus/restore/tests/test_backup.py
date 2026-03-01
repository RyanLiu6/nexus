import json
from unittest.mock import MagicMock, patch

import pytest

from nexus.restore.backup import (
    _get_config_dir_name,
    _get_container_names,
    _get_restore_config,
    get_backrest_config,
    list_backups,
    push_backup,
    restore_backup,
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

SAMPLE_SNAPSHOTS = [
    {"id": "abc123full", "short_id": "abc123", "time": "2024-01-01T00:00:00Z"},
    {"id": "def456full", "short_id": "def456", "time": "2024-01-02T00:00:00Z"},
]


class TestGetConfigDirName:
    def test_get_config_dir_name(self) -> None:
        assert _get_config_dir_name("foundryvtt") == "foundryvtt"

    def test_get_config_dir_name_override(self) -> None:
        assert _get_config_dir_name("backups") == "backrest"

    def test_get_config_dir_name_unknown(self) -> None:
        assert _get_config_dir_name("myservice") == "myservice"


class TestGetContainerNames:
    def test_get_container_names(self) -> None:
        names = _get_container_names("foundryvtt")
        assert names == ["foundryvtt"]

    def test_get_container_names_multi_container(self) -> None:
        names = _get_container_names("sure")
        assert set(names) == {"sure-web", "sure-worker", "sure-db", "sure-redis"}

    def test_get_container_names_nonexistent_service(self) -> None:
        names = _get_container_names("nonexistent-service-xyz")
        assert names == []


class TestGetRestoreConfig:
    @patch("nexus.restore.backup.read_vault")
    @patch.dict("os.environ", {}, clear=True)
    def test_get_restore_config(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {
            "nexus_data_directory": "/data",
            "restic_password": "secret",
        }

        data_dir, password = _get_restore_config()

        assert data_dir == "/data"
        assert password == "secret"

    @patch.dict(
        "os.environ",
        {"NEXUS_DATA_DIRECTORY": "/env-data", "RESTIC_PASSWORD": "env-secret"},
    )
    def test_get_restore_config_from_env(self) -> None:
        data_dir, password = _get_restore_config()

        assert data_dir == "/env-data"
        assert password == "env-secret"

    @patch("nexus.restore.backup.read_vault")
    @patch.dict("os.environ", {"NEXUS_DATA_DIRECTORY": "/env-data"}, clear=True)
    def test_get_restore_config_mixed(self, mock_read_vault: MagicMock) -> None:
        mock_read_vault.return_value = {"restic_password": "vault-secret"}

        data_dir, password = _get_restore_config()

        assert data_dir == "/env-data"
        assert password == "vault-secret"


class TestGetBackrestConfig:
    @patch("nexus.restore.backup.run_command")
    def test_get_backrest_config(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(stdout=json.dumps(SAMPLE_CONFIG))

        config = get_backrest_config()

        assert config == SAMPLE_CONFIG
        mock_run_command.assert_called_once_with(
            ["docker", "exec", "backrest", "cat", "/config/config.json"],
            capture=True,
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
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_list_backups(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(stdout=json.dumps(SAMPLE_SNAPSHOTS))

        result = list_backups(target="local")

        assert len(result) == 2
        assert result[0] == {
            "id": "abc123full",
            "short_id": "abc123",
            "time": "2024-01-01T00:00:00Z",
        }
        assert result[1]["short_id"] == "def456"
        cmd = mock_run_command.call_args[0][0]
        assert "docker" in cmd
        assert "run" in cmd
        assert "--rm" in cmd
        assert "/repos" in cmd
        assert "snapshots" in cmd
        assert "--json" in cmd

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_list_backups_empty(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(stdout="[]")

        result = list_backups()

        assert result == []

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_list_backups_r2_mounts_rclone(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(stdout=json.dumps(SAMPLE_SNAPSHOTS))

        list_backups(target="r2")

        cmd = mock_run_command.call_args[0][0]
        assert any("rclone" in arg for arg in cmd)

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_list_backups_error(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.side_effect = Exception("Container not running")

        result = list_backups()

        assert result == []


class TestRestoreBackup:
    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_restore_backup(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(
            stdout=json.dumps([SAMPLE_SNAPSHOTS[0]])
        )

        restore_backup(snapshot_id="abc123", services=["foundryvtt"], target="local")

        calls = mock_run_command.call_args_list
        stop_call = calls[0][0][0]
        restore_call = calls[1][0][0]
        start_call = calls[2][0][0]

        assert stop_call == ["docker", "stop", "foundryvtt"]
        assert "docker" in restore_call
        assert "run" in restore_call
        assert "--rm" in restore_call
        assert "restore" in restore_call
        assert "abc123" in restore_call
        assert "--target" in restore_call
        assert "/" in restore_call
        assert "--include" in restore_call
        assert "/userdata/foundryvtt" in restore_call
        assert start_call == ["docker", "start", "foundryvtt"]

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_restore_backup_resolves_latest(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(
            stdout=json.dumps([SAMPLE_SNAPSHOTS[0]])
        )

        restore_backup(snapshot_id="latest", services=["foundryvtt"], target="local")

        # First run_command call is the snapshots --latest 1 call
        calls = mock_run_command.call_args_list
        latest_cmd = calls[0][0][0]
        assert "--latest" in latest_cmd
        assert "1" in latest_cmd

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_restore_backup_starts_containers_on_failure(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.side_effect = [
            MagicMock(),  # docker stop
            Exception("Restore failed"),  # docker run restore
            MagicMock(),  # docker start (finally block)
        ]

        with pytest.raises(Exception, match="Restore failed"):
            restore_backup(snapshot_id="abc123", services=["foundryvtt"])

        assert mock_run_command.call_count == 3
        start_call = mock_run_command.call_args_list[2][0][0]
        assert start_call == ["docker", "start", "foundryvtt"]

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_restore_backup_dry_run(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(
            stdout=json.dumps([SAMPLE_SNAPSHOTS[0]])
        )

        restore_backup(snapshot_id="abc123", services=["foundryvtt"], dry_run=True)

        mock_run_command.assert_not_called()

    @patch("nexus.restore.backup.run_command")
    @patch("nexus.restore.backup.get_backrest_config")
    @patch("nexus.restore.backup._get_restore_config")
    def test_restore_backup_r2_mounts_rclone(
        self,
        mock_config_fn: MagicMock,
        mock_backrest_config: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        mock_config_fn.return_value = ("/data", "secret")
        mock_backrest_config.return_value = SAMPLE_CONFIG
        mock_run_command.return_value = MagicMock(
            stdout=json.dumps([SAMPLE_SNAPSHOTS[0]])
        )

        restore_backup(snapshot_id="abc123", services=["foundryvtt"], target="r2")

        restore_call = mock_run_command.call_args_list[1][0][0]
        assert any("rclone" in arg for arg in restore_call)

    def test_restore_backup_invalid_repo(self) -> None:
        with (
            patch(
                "nexus.restore.backup._get_restore_config",
                return_value=("/data", "secret"),
            ),
            patch(
                "nexus.restore.backup.get_backrest_config",
                return_value=SAMPLE_CONFIG,
            ),
        ):
            with pytest.raises(ValueError, match="Repo 'unknown' not found"):
                restore_backup(snapshot_id="abc123", target="unknown")
