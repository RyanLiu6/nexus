import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nexus.cli.restore import _verify_backup, main


class TestVerifyBackup:
    def test_verify_backup_valid(self, tmp_path: Path):
        backup_path = tmp_path / "test.tar.gz"

        with tarfile.open(backup_path, "w:gz") as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(test_file, arcname="test.txt")

        result = _verify_backup(backup_path)

        assert result is True

    def test_verify_backup_invalid(self, tmp_path: Path):
        backup_path = tmp_path / "invalid.tar.gz"
        backup_path.write_bytes(b"not a valid tarfile")

        result = _verify_backup(backup_path)

        assert result is False


class TestMain:
    @patch("nexus.cli.restore.list_backups")
    def test_main_list_backups(self, mock_list: MagicMock, tmp_path: Path):
        backup1 = tmp_path / "backup1.tar.gz"
        backup2 = tmp_path / "backup2.tar.gz"
        backup1.write_bytes(b"x" * 1024 * 1024)
        backup2.write_bytes(b"x" * 2 * 1024 * 1024)

        mock_list.return_value = [backup1, backup2]

        runner = CliRunner()
        result = runner.invoke(main, ["--list"])

        assert result.exit_code == 0
        assert "backup1" in result.output
        assert "backup2" in result.output

    @patch("nexus.cli.restore.list_backups")
    def test_main_list_no_backups(self, mock_list: MagicMock):
        mock_list.return_value = []

        runner = CliRunner()
        result = runner.invoke(main, ["--list"])

        assert result.exit_code == 0
        mock_list.assert_called_once()

    @patch("nexus.cli.restore.BACKUP_DIR")
    @patch("nexus.cli.restore.restore_backup")
    def test_main_restore(
        self, mock_restore: MagicMock, mock_backup_dir: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "test-backup.tar.gz"
        backup_file.touch()

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(main, ["--backup", "test-backup.tar.gz"])

        assert result.exit_code == 0
        mock_restore.assert_called_once()

    @patch("nexus.cli.restore.BACKUP_DIR")
    def test_main_restore_not_found(self, mock_backup_dir: MagicMock, tmp_path: Path):
        mock_backup_dir.__truediv__.return_value = tmp_path / "nonexistent.tar.gz"

        runner = CliRunner()
        result = runner.invoke(main, ["--backup", "nonexistent.tar.gz"])

        assert result.exit_code == 0

    @patch("nexus.cli.restore.BACKUP_DIR")
    def test_main_verify(self, mock_backup_dir: MagicMock, tmp_path: Path):
        backup_file = tmp_path / "test-backup.tar.gz"

        with tarfile.open(backup_file, "w:gz") as tar:
            test_file = tmp_path / "test.txt"
            test_file.write_text("test")
            tar.add(test_file, arcname="test.txt")

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(main, ["--verify", "--backup", "test-backup.tar.gz"])

        assert result.exit_code == 0

    @patch("nexus.cli.restore.BACKUP_DIR")
    def test_main_verify_not_found(self, mock_backup_dir: MagicMock, tmp_path: Path):
        mock_backup_dir.__truediv__.return_value = tmp_path / "nonexistent.tar.gz"

        runner = CliRunner()
        result = runner.invoke(main, ["--verify", "--backup", "nonexistent.tar.gz"])

        assert result.exit_code == 0

    def test_main_no_backup_specified(self):
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0

    @patch("nexus.cli.restore.BACKUP_DIR")
    @patch("nexus.cli.restore.restore_backup")
    def test_main_restore_with_service(
        self, mock_restore: MagicMock, mock_backup_dir: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "test-backup.tar.gz"
        backup_file.touch()

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(
            main, ["--backup", "test-backup.tar.gz", "--service", "plex"]
        )

        assert result.exit_code == 0
        mock_restore.assert_called_once()

    @patch("nexus.cli.restore.BACKUP_DIR")
    @patch("nexus.cli.restore.restore_database")
    def test_main_restore_database(
        self, mock_db_restore: MagicMock, mock_backup_dir: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "test-backup.tar.gz"
        backup_file.touch()

        sql_file = tmp_path / "sure.sql"
        sql_file.touch()

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--backup",
                "test-backup.tar.gz",
                "--db",
                str(sql_file),
                "--service",
                "sure",
            ],
        )

        assert result.exit_code == 0
        mock_db_restore.assert_called_once()

    @patch("nexus.cli.restore.BACKUP_DIR")
    def test_main_restore_database_no_service(
        self, mock_backup_dir: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "test-backup.tar.gz"
        backup_file.touch()

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(
            main, ["--backup", "test-backup.tar.gz", "--db", "/tmp/db.sql"]
        )

        assert result.exit_code == 0

    @patch("nexus.cli.restore.BACKUP_DIR")
    def test_main_restore_database_file_not_found(
        self, mock_backup_dir: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "test-backup.tar.gz"
        backup_file.touch()

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "--backup",
                "test-backup.tar.gz",
                "--db",
                "/nonexistent.sql",
                "--service",
                "sure",
            ],
        )

        assert result.exit_code == 0

    @patch("nexus.cli.restore.BACKUP_DIR")
    @patch("nexus.cli.restore.restore_backup")
    def test_main_restore_dry_run(
        self, mock_restore: MagicMock, mock_backup_dir: MagicMock, tmp_path: Path
    ):
        backup_file = tmp_path / "test-backup.tar.gz"
        backup_file.touch()

        mock_backup_dir.__truediv__.return_value = backup_file

        runner = CliRunner()
        result = runner.invoke(main, ["--backup", "test-backup.tar.gz", "--dry-run"])

        assert result.exit_code == 0
