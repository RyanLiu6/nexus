import json
import logging
import os
from typing import Any

import aiohttp
from discord import Embed, Webhook

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
LOG_FILE = "/tmp/nexus-alerts.log"

logger = logging.getLogger(__name__)


async def send_alert(alert_data: dict[str, Any]) -> None:
    """Send an alert notification to Discord via webhook.

    Creates a formatted embed from the alert data and sends it to the
    configured Discord webhook URL. Also logs the alert to a file.

    Args:
        alert_data: Dictionary containing alert information including
            alertname, status, annotations, and labels.
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("No Discord webhook URL configured")
        return

    try:
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(DISCORD_WEBHOOK_URL, session=session)
            embed = _create_embed(alert_data)
            await webhook.send(embed=embed)
            logger.info(f"Alert sent: {alert_data.get('alertname', 'Unknown')}")

        with open(LOG_FILE, "a") as f:
            f.write(f"{json.dumps(alert_data)}\n")

    except Exception as e:
        logger.error(f"Failed to send alert: {e}")


def _create_embed(alert_data: dict[str, Any]) -> Embed:
    status = alert_data.get("status", "firing").capitalize()

    if status == "firing":
        color = 0xFF0000
        emoji = "🚨"
    else:
        color = 0x00FF00
        emoji = "✅"

    embed = Embed(
        title=f"{emoji} {status}: {alert_data.get('alertname', 'Unknown Alert')}",
        description=alert_data.get("annotations", {}).get(
            "description", "No description"
        ),
        color=color,
    )

    common_labels = alert_data.get("commonLabels", {})
    if common_labels:
        labels_str = "\n".join([f"**{k}**: {v}" for k, v in common_labels.items()])
        embed.add_field(name="Labels", value=labels_str, inline=False)

    severity = alert_data.get("labels", {}).get("severity", "unknown")
    embed.add_field(name="Severity", value=severity, inline=True)

    if "externalURL" in alert_data:
        embed.url = alert_data["externalURL"]

    return embed


class AlertBot:
    def __init__(self) -> None:
        pass

    async def send_alert(self, alert_data: dict[str, Any]) -> None:
        """Send an alert notification to Discord.

        Args:
            alert_data: Dictionary containing alert information.
        """
        await send_alert(alert_data)

    async def start_webhook_server(self, port: int = 8080) -> None:
        """Start an HTTP server to receive alerts from Alertmanager.

        Creates an aiohttp web application that listens for POST requests
        on /webhook and forwards them to Discord.

        Args:
            port: The port to bind the webhook server to.
        """
        from aiohttp import web

        async def handle_webhook(request: web.Request) -> web.Response:
            try:
                alert_data = await request.json()
                logger.debug(f"Received alert: {json.dumps(alert_data, indent=2)}")

                alerts = alert_data if isinstance(alert_data, list) else [alert_data]

                for alert in alerts:
                    await self.send_alert(alert)

                return web.Response(text="OK", status=200)
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                return web.Response(text="Bad Request", status=400)

        app = web.Application()
        app.router.add_post("/webhook", handle_webhook)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)

        logger.info(f"Webhook server started on port {port}")
        await site.start()
