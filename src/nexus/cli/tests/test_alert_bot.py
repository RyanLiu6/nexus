import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from nexus.cli.alert_bot import _run_bot, main


class TestRunBot:
    @pytest.mark.asyncio
    async def test_run_bot(self):
        with patch("nexus.cli.alert_bot.AlertBot") as mock_bot_cls:
            mock_bot = AsyncMock()
            mock_bot_cls.return_value = mock_bot
            
            # Raise exception to break the while True loop
            with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
                with pytest.raises(asyncio.CancelledError):
                    await _run_bot(8080)
            
            mock_bot.start_webhook_server.assert_called_once_with(8080)


class TestMain:
    @patch("nexus.cli.alert_bot.asyncio.run")
    def test_main_default_port(self, mock_run):
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code == 0
        mock_run.assert_called_once()
        
        # Cleanup the coroutine to avoid RuntimeWarning
        coro = mock_run.call_args[0][0]
        coro.close()

    @patch("nexus.cli.alert_bot.asyncio.run")
    def test_main_custom_port(self, mock_run):
        runner = CliRunner()
        result = runner.invoke(main, ["--port", "9090"])

        assert result.exit_code == 0
        mock_run.assert_called_once()

        # Cleanup the coroutine to avoid RuntimeWarning
        coro = mock_run.call_args[0][0]
        coro.close()
