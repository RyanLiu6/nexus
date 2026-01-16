import subprocess
from unittest.mock import MagicMock, patch

import pytest

from nexus.operations.maintenance import (
    _run_command,
    check_container_status,
    check_disk_space,
    check_service_logs,
    cleanup_old_images,
    cleanup_old_volumes,
    daily_tasks,
    monthly_tasks,
    verify_backups,
    weekly_tasks,
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


class TestRunCommand:
    def test_run_command_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="output", returncode=0)
            result = _run_command(["echo", "test"], "Test command")
            assert result.stdout == "output"
            mock_run.assert_called_once()

    def test_run_command_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "cmd", stderr="error message"
            )
            with pytest.raises(subprocess.CalledProcessError):
                _run_command(["false"], "Failing command")


class TestCheckServiceLogs:
    def test_check_service_logs(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="info message\nERROR something", returncode=0
            )
            check_service_logs()
            assert mock_run.call_count == 4

    def test_check_service_logs_no_errors(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="all good\nno issues", returncode=0
            )
            check_service_logs()


class TestCleanupOldImages:
    def test_cleanup_old_images(self, mock_run_command: MagicMock):
        mock_run_command.return_value = MagicMock(stdout="Total reclaimed space: 1GB")
        cleanup_old_images()
        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert "docker" in args
        assert "image" in args
        assert "prune" in args


class TestCleanupOldVolumes:
    def test_cleanup_old_volumes(self, mock_run_command: MagicMock):
        mock_run_command.return_value = MagicMock(stdout="Total reclaimed space: 500MB")
        cleanup_old_volumes()
        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert "docker" in args
        assert "volume" in args
        assert "prune" in args


class TestDailyTasks:
    def test_daily_tasks(self, mock_run_command: MagicMock):
        mock_run_command.return_value = MagicMock(
            stdout="Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1       100G   50G   50G  50% /",
            returncode=0,
        )

        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = MagicMock(stdout="no errors")
            daily_tasks()

        assert mock_run_command.call_count >= 2


class TestWeeklyTasks:
    def test_weekly_tasks(self, mock_run_command: MagicMock, tmp_path):
        mock_run_command.return_value = MagicMock(stdout="reclaimed space")

        backup_dir = tmp_path / "nexus-backups"
        backup_dir.mkdir()
        (backup_dir / "nexus-backup-20240101.tar.gz").touch()

        with patch("nexus.operations.maintenance.Path.home", return_value=tmp_path):
            weekly_tasks()

        assert mock_run_command.call_count == 2


class TestMonthlyTasks:
    def test_monthly_tasks(self):
        monthly_tasks()


class TestCheckDiskSpaceCritical:
    def test_check_disk_space_critical(self, mock_run_command: MagicMock):
        mock_run_command.return_value = MagicMock(
            stdout="Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1       100G   95G   5G  95% /",
            returncode=0,
        )

        result = check_disk_space()

        assert result["usage_percent"] == 95

    def test_check_disk_space_empty_output(self, mock_run_command: MagicMock):
        mock_run_command.return_value = MagicMock(stdout="", returncode=0)

        result = check_disk_space()

        assert result == {}
