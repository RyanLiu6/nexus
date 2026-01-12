import subprocess
from unittest.mock import patch

import pytest

from nexus.deploy.docker import run_docker_compose


@patch("nexus.deploy.docker.run_command")
def test_run_docker_compose_up(mock_run_command, tmp_path):
    mock_run_command.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    result = run_docker_compose(tmp_path, action="up")

    assert result.returncode == 0
    args = mock_run_command.call_args[0][0]
    assert args == ["docker", "compose", "up", "-d"]


@patch("nexus.deploy.docker.run_command")
def test_run_docker_compose_down(mock_run_command, tmp_path):
    mock_run_command.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    run_docker_compose(tmp_path, action="down")

    args = mock_run_command.call_args[0][0]
    assert args == ["docker", "compose", "down"]


@patch("nexus.deploy.docker.run_command")
def test_run_docker_compose_ps(mock_run_command, tmp_path):
    mock_run_command.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    run_docker_compose(tmp_path, action="ps")

    args = mock_run_command.call_args[0][0]
    assert args == ["docker", "compose", "ps"]


@patch("nexus.deploy.docker.run_command")
def test_run_docker_compose_logs(mock_run_command, tmp_path):
    mock_run_command.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    run_docker_compose(tmp_path, action="logs")

    args = mock_run_command.call_args[0][0]
    assert args == ["docker", "compose", "logs"]


@patch("nexus.deploy.docker.run_command")
def test_run_docker_compose_custom_action(mock_run_command, tmp_path):
    mock_run_command.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    run_docker_compose(tmp_path, action="restart")

    args = mock_run_command.call_args[0][0]
    assert args == ["docker", "compose", "restart"]


@patch("nexus.deploy.docker.run_command")
def test_run_docker_compose_with_extra_args(mock_run_command, tmp_path):
    mock_run_command.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )

    extra = ["--build", "--force-recreate"]
    run_docker_compose(tmp_path, action="up", extra_args=extra)

    args = mock_run_command.call_args[0][0]
    assert args == ["docker", "compose", "up", "-d", "--build", "--force-recreate"]


def test_run_docker_compose_path_not_found():
    from pathlib import Path

    with pytest.raises(FileNotFoundError):
        run_docker_compose(Path("/nonexistent/path"))


def test_run_docker_compose_dry_run(tmp_path):
    result = run_docker_compose(tmp_path, action="up", dry_run=True)

    assert result.returncode == 0
    assert result.args == ["docker", "compose", "up", "-d"]
