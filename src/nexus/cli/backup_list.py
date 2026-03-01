import logging

import click

from nexus.restore.backup import list_backups

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--target",
    type=click.Choice(["local", "r2"]),
    default="local",
    show_default=True,
    help="Repository to list snapshots from.",
)
def main(target: str) -> None:
    """List available restic backup snapshots.

    Args:
        target: Which repository to list snapshots from: "local" or "r2".
    """
    snapshots = list_backups(target=target)
    if not snapshots:
        logger.info("No backup snapshots found")
        return

    print(f"\nAvailable backup snapshots (repo: {target}):")
    for snap in snapshots:
        print(f"  {snap['short_id']}  {snap['time']}  (full id: {snap['id'][:16]}...)")


if __name__ == "__main__":
    main()
