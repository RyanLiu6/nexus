import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from nexus.deploy.ansible import run_ansible


class TestRunAnsible:
    @patch("nexus.deploy.ansible.run_command")
    @patch("nexus.deploy.ansible.ANSIBLE_PATH")
    def test_run_ansible(
        self, mock_path: MagicMock, mock_run_command: MagicMock, tmp_path: Path
    ) -> None:
        playbook = tmp_path / "playbook.yml"
        playbook.touch()

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_path.__truediv__.side_effect = path_side_effect

        run_ansible(["plex", "jellyfin"])

        mock_run_command.assert_called_once()
        args = mock_run_command.call_args[0][0]
        assert args[0] == "ansible-playbook"
        assert "plex,jellyfin" in args[3]

    @patch("nexus.deploy.ansible.ANSIBLE_PATH")
    def test_run_ansible_playbook_not_found(
        self, mock_path: MagicMock, tmp_path: Path
    ) -> None:
        mock_path.__truediv__.return_value = tmp_path / "playbook.yml"

        with pytest.raises(FileNotFoundError):
            run_ansible(["plex"])

    @patch("nexus.deploy.ansible.ANSIBLE_PATH")
    def test_run_ansible_dry_run(self, mock_path: MagicMock, tmp_path: Path) -> None:
        playbook = tmp_path / "playbook.yml"
        playbook.touch()

        mock_path.__truediv__.return_value = playbook

        run_ansible(["plex", "jellyfin"], dry_run=True)

    @patch("nexus.deploy.ansible.run_command")
    @patch("nexus.deploy.ansible.ANSIBLE_PATH")
    def test_run_ansible_command_failure(
        self, mock_path: MagicMock, mock_run_command: MagicMock, tmp_path: Path
    ) -> None:
        playbook = tmp_path / "playbook.yml"
        playbook.touch()

        def path_side_effect(arg: str) -> Path:
            return tmp_path / arg

        mock_path.__truediv__.side_effect = path_side_effect
        mock_run_command.side_effect = subprocess.CalledProcessError(
            1, "ansible-playbook"
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_ansible(["plex"])
