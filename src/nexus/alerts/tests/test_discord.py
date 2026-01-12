from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from discord import Embed

from nexus.alerts.discord import AlertBot, _create_embed, send_alert


class TestCreateEmbed:
    def test_create_embed_firing(self):
        alert_data = {
            "status": "firing",
            "alertname": "TestAlert",
            "annotations": {"description": "Test description"},
            "labels": {"severity": "critical"},
            "commonLabels": {"app": "nexus"},
        }

        embed = _create_embed(alert_data)

        assert isinstance(embed, Embed)
        assert "Firing" in embed.title
        assert "TestAlert" in embed.title
        assert embed.color is not None

    def test_create_embed_resolved(self):
        alert_data = {
            "status": "resolved",
            "alertname": "TestAlert",
            "annotations": {"description": "Issue resolved"},
            "labels": {"severity": "warning"},
        }

        embed = _create_embed(alert_data)

        assert "Resolved" in embed.title
        assert embed.color is not None

    def test_create_embed_with_external_url(self):
        alert_data = {
            "status": "firing",
            "alertname": "TestAlert",
            "externalURL": "https://prometheus.example.com",
        }

        embed = _create_embed(alert_data)

        assert embed.url == "https://prometheus.example.com"

    def test_create_embed_default_values(self):
        alert_data = {}

        embed = _create_embed(alert_data)

        assert "Unknown Alert" in embed.title
        assert "No description" in embed.description

    def test_create_embed_with_common_labels(self):
        alert_data = {
            "status": "firing",
            "alertname": "TestAlert",
            "commonLabels": {"app": "nexus", "env": "prod"},
        }

        embed = _create_embed(alert_data)

        assert len(embed.fields) >= 1
        labels_field = next((f for f in embed.fields if f.name == "Labels"), None)
        assert labels_field is not None


class TestSendAlert:
    @pytest.mark.asyncio
    async def test_send_alert_no_webhook_url(self):
        with patch("nexus.alerts.discord.DISCORD_WEBHOOK_URL", None):
            await send_alert({"alertname": "Test"})

    @pytest.mark.asyncio
    async def test_send_alert_success(self, tmp_path):
        mock_webhook = AsyncMock()
        mock_session = MagicMock()

        with (
            patch(
                "nexus.alerts.discord.DISCORD_WEBHOOK_URL",
                "https://discord.com/webhook",
            ),
            patch("nexus.alerts.discord.LOG_FILE", str(tmp_path / "alerts.log")),
            patch("aiohttp.ClientSession") as mock_client,
            patch("nexus.alerts.discord.Webhook") as mock_webhook_class,
        ):
            mock_client.return_value.__aenter__.return_value = mock_session
            mock_client.return_value.__aexit__.return_value = None
            mock_webhook_class.from_url.return_value = mock_webhook

            alert_data = {"alertname": "TestAlert", "status": "firing"}
            await send_alert(alert_data)

            mock_webhook.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert_exception(self):
        with (
            patch(
                "nexus.alerts.discord.DISCORD_WEBHOOK_URL",
                "https://discord.com/webhook",
            ),
            patch("aiohttp.ClientSession") as mock_client,
        ):
            mock_client.return_value.__aenter__.side_effect = Exception(
                "Connection error"
            )

            await send_alert({"alertname": "Test"})


class TestAlertBot:
    def test_init(self):
        bot = AlertBot()
        assert bot is not None

    @pytest.mark.asyncio
    async def test_send_alert(self):
        bot = AlertBot()

        with patch(
            "nexus.alerts.discord.send_alert", new_callable=AsyncMock
        ) as mock_send:
            await bot.send_alert({"alertname": "Test"})
            mock_send.assert_called_once_with({"alertname": "Test"})

    @pytest.mark.asyncio
    async def test_start_webhook_server(self):
        bot = AlertBot()

        with patch("aiohttp.web.AppRunner") as mock_runner:
            mock_runner_instance = AsyncMock()
            mock_runner.return_value = mock_runner_instance

            with patch("aiohttp.web.TCPSite") as mock_site:
                mock_site_instance = AsyncMock()
                mock_site.return_value = mock_site_instance

                await bot.start_webhook_server(port=9090)

                mock_runner_instance.setup.assert_called_once()
                mock_site_instance.start.assert_called_once()
