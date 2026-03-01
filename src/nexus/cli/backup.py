import logging

import click

from nexus.restore.backup import push_backup

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--target",
    type=click.Choice(["local", "r2", "all"]),
    default="all",
    show_default=True,
    help="Repository to back up.",
)
@click.option("--dry-run", is_flag=True, help="Preview backup without executing.")
def main(target: str, dry_run: bool) -> None:
    """Trigger a restic backup for Nexus repositories.

    Reads repo URIs and retention policies from the Backrest configuration,
    runs a backup followed by pruning to enforce retention limits.

    Args:
        target: Which repositories to back up: "local", "r2", or "all".
        dry_run: Preview backup commands without executing them.
    """
    try:
        push_backup(target=target, dry_run=dry_run)
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
