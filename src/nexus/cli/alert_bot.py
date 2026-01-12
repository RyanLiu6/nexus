import asyncio
import logging

import click

from nexus.alerts.discord import AlertBot

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def _run_bot(port: int) -> None:
    bot = AlertBot()
    await bot.start_webhook_server(port)
    while True:
        await asyncio.sleep(3600)


@click.command()
@click.option("--port", type=int, default=8080, help="Webhook server port.")
def main(port: int) -> None:
    """Run the Discord alert bot."""
    asyncio.run(_run_bot(port))


if __name__ == "__main__":
    main()
