from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.restore import _verify_backup, main


class TestVerifyBackup:
    @patch("nexus.cli.restore.run_command")
    def test_verify_backup(self, mock_run_command: MagicMock) -> None:
        result = _verify_backup()

        assert result is True
        mock_run_command.assert_called_once()

    @patch("nexus.cli.restore.run_command")
    def test_verify_backup_failure(self, mock_run_command: MagicMock) -> None:
        mock_run_command.side_effect = Exception("Check failed")

        result = _verify_backup()

        assert result is False


class TestMain:
    @patch("nexus.cli.restore.restore_backup")
    def test_main(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--snapshot", "abc123", "--yes"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(
            snapshot_id="abc123",
            services=None,
            target="local",
            dry_run=False,
        )

    @patch("nexus.cli.restore.restore_backup")
    def test_main_with_service(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["--snapshot", "abc123", "--service", "foundryvtt", "--yes"]
        )

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(
            snapshot_id="abc123",
            services=["foundryvtt"],
            target="local",
            dry_run=False,
        )

    @patch("nexus.cli.restore.restore_backup")
    def test_main_with_multiple_services(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--snapshot",
                "abc123",
                "--service",
                "foundryvtt",
                "--service",
                "plex",
                "--yes",
            ],
        )

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(
            snapshot_id="abc123",
            services=["foundryvtt", "plex"],
            target="local",
            dry_run=False,
        )

    @patch("nexus.cli.restore.restore_backup")
    def test_main_dry_run(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--snapshot", "abc123", "--dry-run"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(
            snapshot_id="abc123",
            services=None,
            target="local",
            dry_run=True,
        )

    @patch("nexus.cli.restore.restore_backup")
    def test_main_r2_target(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["--snapshot", "abc123", "--target", "r2", "--yes"]
        )

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(
            snapshot_id="abc123",
            services=None,
            target="r2",
            dry_run=False,
        )

    @patch("nexus.cli.restore.restore_backup")
    def test_main_default_snapshot_is_latest(self, mock_restore: MagicMock) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--yes"])

        assert result.exit_code == 0
        mock_restore.assert_called_once_with(
            snapshot_id="latest",
            services=None,
            target="local",
            dry_run=False,
        )

    @patch("nexus.cli.restore._get_container_names")
    @patch("nexus.cli.restore.restore_backup")
    def test_main_confirmation_prompt_yes(
        self, mock_restore: MagicMock, mock_containers: MagicMock
    ) -> None:
        mock_containers.return_value = ["foundryvtt"]

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--snapshot", "abc123", "--service", "foundryvtt"],
            input="y\n",
        )

        assert result.exit_code == 0
        assert "foundryvtt" in result.output
        mock_restore.assert_called_once()

    @patch("nexus.cli.restore._get_container_names")
    @patch("nexus.cli.restore.restore_backup")
    def test_main_confirmation_prompt_no(
        self, mock_restore: MagicMock, mock_containers: MagicMock
    ) -> None:
        mock_containers.return_value = ["foundryvtt"]

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--snapshot", "abc123", "--service", "foundryvtt"],
            input="n\n",
        )

        assert result.exit_code != 0
        mock_restore.assert_not_called()
