import logging

import click

from nexus.operations import daily_tasks, monthly_tasks, weekly_tasks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@click.command()
@click.option("--daily", is_flag=True, help="Run daily maintenance tasks.")
@click.option("--weekly", is_flag=True, help="Run weekly maintenance tasks.")
@click.option("--monthly", is_flag=True, help="Run monthly maintenance tasks.")
@click.option("--all", "run_all", is_flag=True, help="Run all maintenance tasks.")
def main(daily: bool, weekly: bool, monthly: bool, run_all: bool) -> None:
    """Execute scheduled maintenance tasks for Nexus infrastructure.

    Runs maintenance operations grouped by frequency. Tasks include log rotation,
    Docker image cleanup, backup verification, and system health checks.

    Args:
        daily: Run daily maintenance tasks (log rotation, temp cleanup).
        weekly: Run weekly maintenance tasks (image pruning, backup checks).
        monthly: Run monthly maintenance tasks (full system audit).
        run_all: Run all maintenance tasks regardless of schedule.
    """
    if run_all or daily:
        daily_tasks()

    if run_all or weekly:
        weekly_tasks()

    if run_all or monthly:
        monthly_tasks()

    if not (daily or weekly or monthly or run_all):
        logger.error(
            "Please specify a task type: --daily, --weekly, --monthly, or --all"
        )
        return

    logger.info("🎉 Operations complete!")


if __name__ == "__main__":
    main()
