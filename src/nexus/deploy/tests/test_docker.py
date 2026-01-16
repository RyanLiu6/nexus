import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexus.deploy.docker import run_docker_compose


class TestRunDockerCompose:
    @patch("nexus.deploy.docker.run_command")
    def test_run_docker_compose_up(self, mock_run_command: MagicMock, tmp_path: Path):
        mock_run_command.return_value = subprocess.CompletedProcess(
            args=[], returncode=0
        )

        result = run_docker_compose(tmp_path, action="up")

        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert args == ["docker", "compose", "up", "-d"]
        assert result.returncode == 0

    @patch("nexus.deploy.docker.run_command")
    def test_run_docker_compose_down(self, mock_run_command: MagicMock, tmp_path: Path):
        mock_run_command.return_value = subprocess.CompletedProcess(
            args=[], returncode=0
        )

        run_docker_compose(tmp_path, action="down")

        args = mock_run_command.call_args[0][0]
        assert args == ["docker", "compose", "down"]

    @patch("nexus.deploy.docker.run_command")
    def test_run_docker_compose_ps(self, mock_run_command: MagicMock, tmp_path: Path):
        mock_run_command.return_value = subprocess.CompletedProcess(
            args=[], returncode=0
        )

        run_docker_compose(tmp_path, action="ps")

        args = mock_run_command.call_args[0][0]
        assert args == ["docker", "compose", "ps"]

    @patch("nexus.deploy.docker.run_command")
    def test_run_docker_compose_logs(self, mock_run_command: MagicMock, tmp_path: Path):
        mock_run_command.return_value = subprocess.CompletedProcess(
            args=[], returncode=0
        )

        run_docker_compose(tmp_path, action="logs")

        args = mock_run_command.call_args[0][0]
        assert args == ["docker", "compose", "logs"]

    @patch("nexus.deploy.docker.run_command")
    def test_run_docker_compose_custom_action(
        self, mock_run_command: MagicMock, tmp_path: Path
    ):
        mock_run_command.return_value = subprocess.CompletedProcess(
            args=[], returncode=0
        )

        run_docker_compose(tmp_path, action="restart")

        args = mock_run_command.call_args[0][0]
        assert args == ["docker", "compose", "restart"]

    @patch("nexus.deploy.docker.run_command")
    def test_run_docker_compose_extra_args(
        self, mock_run_command: MagicMock, tmp_path: Path
    ):
        mock_run_command.return_value = subprocess.CompletedProcess(
            args=[], returncode=0
        )

        run_docker_compose(tmp_path, action="logs", extra_args=["--tail", "100"])

        args = mock_run_command.call_args[0][0]
        assert args == ["docker", "compose", "logs", "--tail", "100"]

    def test_run_docker_compose_path_not_found(self):
        fake_path = Path("/nonexistent/path")

        with pytest.raises(FileNotFoundError):
            run_docker_compose(fake_path)

    def test_run_docker_compose_dry_run(self, tmp_path: Path):
        result = run_docker_compose(tmp_path, action="up", dry_run=True)

        assert result.returncode == 0
        assert result.args == ["docker", "compose", "up", "-d"]

    def test_run_docker_compose_dry_run_with_extra_args(self, tmp_path: Path):
        result = run_docker_compose(
            tmp_path, action="logs", extra_args=["--follow"], dry_run=True
        )

        assert result.returncode == 0
        assert result.args == ["docker", "compose", "logs", "--follow"]
