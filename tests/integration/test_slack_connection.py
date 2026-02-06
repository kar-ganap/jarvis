from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(
    not os.environ.get("SLACK_BOT_TOKEN") or not os.environ.get("SLACK_APP_TOKEN"),
    reason="SLACK_BOT_TOKEN and SLACK_APP_TOKEN not set",
)
class TestSlackConnection:
    @pytest.mark.timeout(15)
    async def test_socket_mode_connects(self):
        """Smoke test: Socket Mode connects without error."""
        from slack_bolt.adapter.socket_mode.async_handler import (
            AsyncSocketModeHandler,
        )
        from slack_bolt.app.async_app import AsyncApp

        app = AsyncApp(token=os.environ["SLACK_BOT_TOKEN"])
        handler = AsyncSocketModeHandler(
            app=app, app_token=os.environ["SLACK_APP_TOKEN"]
        )

        # connect_async establishes the WebSocket connection
        await handler.connect_async()
        assert handler.client is not None

        # Clean up
        await handler.close_async()
