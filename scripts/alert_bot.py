#!/usr/bin/env python3
import asyncio
import logging

import click

from nexus.alerts.discord import AlertBot

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def run_bot(port: int) -> None:
    """Run the alert bot.

    Args:
        port: The port to bind the webhook server to.
    """
    bot = AlertBot()
    # Keep the server running
    await bot.start_webhook_server(port)
    # This is a bit hacky, start_webhook_server is async but returns after starting.
    # We need to keep the loop alive.
    # start_webhook_server in discord.py returns Site, but doesn't block forever?
    # Wait, `await site.start()` starts it. `web.TCPSite` doesn't block.
    # So we need to sleep forever.
    while True:
        await asyncio.sleep(3600)


@click.command()
@click.option("--port", type=int, default=8080, help="Webhook server port")
@click.option("--config", type=str, help="Path to config file (unused)")
def main(port: int, config: str) -> None:
    """Run the alert bot.

    Args:
        port: The port to bind the webhook server to.
        config: Path to config file (unused).
    """
    asyncio.run(run_bot(port))


if __name__ == "__main__":
    main()
