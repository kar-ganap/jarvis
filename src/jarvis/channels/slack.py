from __future__ import annotations

import structlog
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.app.async_app import AsyncApp

from jarvis.channels.base import (
    Channel,
    ChannelMessage,
    ChannelType,
    ChannelUser,
    InboundHandler,
    OutboundMessage,
)

log = structlog.get_logger()


class SlackChannel(Channel):
    """Slack channel using Socket Mode (WebSocket, no public URL needed)."""

    def __init__(self, bot_token: str, app_token: str) -> None:
        self._bot_token = bot_token
        self._app_token = app_token
        self._app: AsyncApp | None = None
        self._handler: AsyncSocketModeHandler | None = None
        self._on_message: InboundHandler | None = None

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.SLACK

    async def start(self, on_message: InboundHandler) -> None:
        """Connect to Slack via Socket Mode and listen for messages."""
        self._on_message = on_message
        self._app = AsyncApp(token=self._bot_token)

        @self._app.message()
        async def handle_message(message, client):
            if self._should_skip(message):
                return
            await self._dispatch(message, client)

        @self._app.event("app_mention")
        async def handle_mention(event, client):
            if self._should_skip(event):
                return
            await self._dispatch(event, client)

        self._handler = AsyncSocketModeHandler(
            app=self._app, app_token=self._app_token
        )

        log.info("slack.starting")
        await self._handler.start_async()

    def _should_skip(self, event: dict) -> bool:
        """Return True if this event should be ignored (bot messages)."""
        if event.get("bot_id"):
            return True
        if event.get("subtype") in (
            "bot_message",
            "message_changed",
            "message_deleted",
        ):
            return True
        return False

    async def _dispatch(self, event: dict, client) -> None:
        """Normalize Slack event to ChannelMessage and forward."""
        user_id = event.get("user", "")
        text = event.get("text", "")
        channel_id = event.get("channel", "")

        display_name = await self._resolve_user_name(client, user_id)

        msg = ChannelMessage(
            channel_type=ChannelType.SLACK,
            user=ChannelUser(id=channel_id, display_name=display_name),
            text=text,
            raw=event,
        )

        log.info(
            "slack.inbound",
            user=display_name,
            channel=channel_id,
        )

        if self._on_message:
            await self._on_message(msg)

    async def _resolve_user_name(self, client, user_id: str) -> str:
        """Resolve Slack user ID to display name."""
        try:
            info = await client.users_info(user=user_id)
            profile = info["user"]["profile"]
            return (
                profile.get("display_name")
                or profile.get("real_name")
                or "User"
            )
        except Exception:
            log.debug("slack.user_resolve_failed", user_id=user_id)
            return "User"

    async def stop(self) -> None:
        """Disconnect from Slack."""
        if self._handler:
            await self._handler.close_async()
        log.info("slack.stopped")

    async def send(self, message: OutboundMessage) -> None:
        """Send a message to a Slack channel/DM."""
        if self._app:
            await self._app.client.chat_postMessage(
                channel=message.recipient_id,
                text=message.text,
            )
