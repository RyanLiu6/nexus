#!/usr/bin/env python3
"""Alertmanager to Discord webhook bridge.

Receives webhooks from Alertmanager and forwards them to Discord
with properly formatted embeds.
"""

import asyncio
import json
import logging
import os

import aiohttp
from aiohttp import web
from discord import Embed, Webhook

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_embed(alert: dict) -> Embed:
    """Create a Discord embed from an Alertmanager alert.

    Args:
        alert: Alertmanager alert dictionary containing status, labels,
            and annotations.

    Returns:
        Discord Embed object with alert details, color-coded by status.
    """
    status = alert.get("status", "firing")
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})

    if status == "firing":
        color = 0xFF0000  # Red
        emoji = "\U0001f6a8"  # Siren
    else:
        color = 0x00FF00  # Green
        emoji = "\u2705"  # Check mark

    alert_name = labels.get("alertname", "Unknown Alert")
    severity = labels.get("severity", "unknown")

    description = annotations.get("description") or annotations.get(
        "summary", "No description"
    )
    embed = Embed(
        title=f"{emoji} {status.upper()}: {alert_name}",
        description=description,
        color=color,
    )

    embed.add_field(name="Severity", value=severity, inline=True)

    if "instance" in labels:
        embed.add_field(name="Instance", value=labels["instance"], inline=True)

    if "job" in labels:
        embed.add_field(name="Job", value=labels["job"], inline=True)

    return embed


async def send_to_discord(alerts: list[dict]) -> None:
    """Send alerts to Discord via webhook.

    Args:
        alerts: List of Alertmanager alert dictionaries to forward.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL not configured, skipping")
        return

    try:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(DISCORD_WEBHOOK_URL, session=session)

            for alert in alerts:
                embed = create_embed(alert)
                await webhook.send(embed=embed, username="Nexus Alerts")
                alert_name = alert.get("labels", {}).get("alertname", "unknown")
                logger.info(f"Sent alert: {alert_name}")

    except Exception as e:
        logger.error(f"Failed to send to Discord: {e}")


async def handle_webhook(request: web.Request) -> web.Response:
    """Handle incoming Alertmanager webhook.

    Args:
        request: aiohttp request containing the Alertmanager JSON payload.

    Returns:
        HTTP 200 on success, 400 for invalid JSON, 500 on internal errors.
    """
    try:
        data = await request.json()
        logger.debug(f"Received webhook: {json.dumps(data, indent=2)}")

        alerts = data.get("alerts", [])
        if alerts:
            await send_to_discord(alerts)

        return web.Response(text="OK", status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return web.Response(text="Invalid JSON", status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return web.Response(text="Internal Error", status=500)


async def handle_health(request: web.Request) -> web.Response:
    """Health check endpoint.

    Args:
        request: aiohttp request (unused).

    Returns:
        HTTP 200 with "OK" body.
    """
    return web.Response(text="OK", status=200)


async def main() -> None:
    """Start the webhook server.

    Configures routes for /webhook and /health, then binds to the port
    specified by the PORT environment variable (default 8080).
    """
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)

    logger.info(f"Starting alert-bot webhook server on port {port}")
    if DISCORD_WEBHOOK_URL:
        logger.info("Discord webhook URL configured")
    else:
        logger.warning("DISCORD_WEBHOOK_URL not set - alerts will not be forwarded")

    await site.start()

    # Keep running
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
