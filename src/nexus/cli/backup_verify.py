import logging

import click

from nexus.utils import run_command

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@click.command()
def main() -> None:
    """Verify backup repository integrity."""
    try:
        run_command(["docker", "exec", "backrest", "restic", "-r", "/repos", "check"])
        logger.info("Backup repositories verified successfully")
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
