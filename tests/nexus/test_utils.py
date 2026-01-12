import subprocess
from unittest.mock import MagicMock, patch

import pytest

from nexus.utils import run_command


@patch("nexus.utils.subprocess.run")
def test_run_command(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["echo", "test"], returncode=0, stdout="test\n", stderr=""
    )

    result = run_command(["echo", "test"])

    assert result.returncode == 0
    mock_run.assert_called_once()


@patch("nexus.utils.subprocess.run")
def test_run_command_with_capture(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["echo", "output"], returncode=0, stdout="output\n", stderr=""
    )

    result = run_command(["echo", "output"], capture=True)

    assert result.stdout == "output\n"
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["capture_output"] is True


@patch("nexus.utils.subprocess.run")
def test_run_command_with_custom_cwd(mock_run, tmp_path):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ls"], returncode=0, stdout="", stderr=""
    )

    run_command(["ls"], cwd=tmp_path)

    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["cwd"] == tmp_path


@patch("nexus.utils.subprocess.run")
def test_run_command_check_false(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["false"], returncode=1, stdout="", stderr=""
    )

    result = run_command(["false"], check=False)

    assert result.returncode == 1
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["check"] is False


@patch("nexus.utils.subprocess.run")
def test_run_command_failure_raises(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["bad"], stderr="error message"
    )

    with pytest.raises(subprocess.CalledProcessError):
        run_command(["bad"])


@patch("nexus.utils.subprocess.run")
def test_run_command_with_stdin(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=["cat"], returncode=0, stdout="", stderr=""
    )
    mock_stdin = MagicMock()

    run_command(["cat"], stdin=mock_stdin)

    call_kwargs = mock_run.call_args[1]
    assert call_kwargs["stdin"] == mock_stdin
