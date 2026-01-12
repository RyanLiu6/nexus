from unittest.mock import MagicMock, patch

import pytest

from nexus.operations.maintenance import (
    check_container_status,
    check_disk_space,
    verify_backups,
)


@pytest.fixture
def mock_run_command():
    with patch("nexus.operations.maintenance._run_command") as mock:
        yield mock


class TestCheckContainerStatus:
    def test_check_container_status(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(
            stdout="container1\tUp 2 hours (healthy)\ncontainer2\tUp 1 hour",
            returncode=0,
        )

        result = check_container_status()

        assert result is True
        mock_run_command.assert_called_once()

    def test_check_container_status_with_unhealthy(
        self, mock_run_command: MagicMock
    ) -> None:
        mock_run_command.return_value = MagicMock(
            stdout="container1\tExited (1) 2 hours ago\ncontainer2\tUp 1 hour",
            returncode=0,
        )

        result = check_container_status()

        assert result is False


class TestCheckDiskSpace:
    def test_check_disk_space(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(
            stdout="Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1       100G   50G   50G  50% /",
            returncode=0,
        )

        result = check_disk_space()

        assert result["total"] == "100G"
        assert result["used"] == "50G"
        assert result["available"] == "50G"
        assert result["usage_percent"] == 50

    def test_check_disk_space_high_usage(self, mock_run_command: MagicMock) -> None:
        mock_run_command.return_value = MagicMock(
            stdout="Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1       100G   85G   15G  85% /",
            returncode=0,
        )

        result = check_disk_space()

        assert result["usage_percent"] == 85


class TestVerifyBackups:
    def test_verify_backups(self, tmp_path) -> None:
        backup_dir = tmp_path / "nexus-backups"
        backup_dir.mkdir()

        for i in range(3):
            (backup_dir / f"nexus-backup-2024010{i}.tar.gz").touch()

        with patch("nexus.operations.maintenance.Path.home", return_value=tmp_path):
            result = verify_backups()

        assert result is True

    def test_verify_backups_no_directory(self, tmp_path) -> None:
        with patch("nexus.operations.maintenance.Path.home", return_value=tmp_path):
            result = verify_backups()

        assert result is False

    def test_verify_backups_empty_directory(self, tmp_path) -> None:
        backup_dir = tmp_path / "nexus-backups"
        backup_dir.mkdir()

        with patch("nexus.operations.maintenance.Path.home", return_value=tmp_path):
            result = verify_backups()

        assert result is False
