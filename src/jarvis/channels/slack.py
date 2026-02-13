from __future__ import annotations

import aiohttp
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

        @self._app.event("message")
        async def handle_message(event, client):
            if self._should_skip(event):
                return
            await self._dispatch(event, client)

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
        """Return True if this event should be ignored."""
        if event.get("bot_id"):
            return True
        subtype = event.get("subtype")
        # Allow regular messages (no subtype) and file_share (audio clips);
        # skip all other subtypes (bot_message, message_changed, etc.)
        if subtype and subtype != "file_share":
            return True
        return False

    async def _dispatch(self, event: dict, client) -> None:
        """Normalize Slack event to ChannelMessage and forward."""
        user_id = event.get("user", "")
        text = event.get("text", "")
        channel_id = event.get("channel", "")

        display_name = await self._resolve_user_name(client, user_id)

        # Check for audio file attachments
        # Slack native clips: audio/mp4. Re-uploaded clips: video/mp4.
        audio_data = None
        audio_mime = None
        for f in event.get("files", []):
            mime = f.get("mimetype", "")
            name = f.get("name", "")
            is_audio = mime.startswith("audio/") or (
                mime == "video/mp4" and name.startswith("audio_message")
            )
            if is_audio:
                url = f.get("url_private_download", "")
                if url:
                    audio_data = await self._download_slack_file(url)
                    audio_mime = mime
                break

        msg = ChannelMessage(
            channel_type=ChannelType.SLACK,
            user=ChannelUser(id=channel_id, display_name=display_name),
            text=text,
            raw=event,
            audio_data=audio_data,
            audio_mime=audio_mime,
        )

        log.info(
            "slack.inbound",
            user=display_name,
            channel=channel_id,
            has_audio=audio_data is not None,
        )

        if self._on_message:
            await self._on_message(msg)

    async def _download_slack_file(self, url: str) -> bytes:
        """Download a file from Slack using bot token auth.

        Slack's url_private_download redirects to a CDN. aiohttp strips
        the Authorization header on cross-origin redirects, so we handle
        the redirect manually: first hop needs auth, CDN hop does not.
        """
        headers = {"Authorization": f"Bearer {self._bot_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, headers=headers, allow_redirects=False,
            ) as resp:
                if resp.status in (301, 302, 303, 307, 308):
                    cdn_url = resp.headers["Location"]
                    async with session.get(cdn_url) as cdn_resp:
                        cdn_resp.raise_for_status()
                        return await cdn_resp.read()
                resp.raise_for_status()
                return await resp.read()

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
        if not self._app:
            return

        # Upload audio file if present (needs files:write scope)
        if message.audio_data:
            ext = "mp3" if "mp3" in (message.audio_mime or "") else "ogg"
            try:
                await self._app.client.files_upload_v2(
                    channel=message.recipient_id,
                    content=message.audio_data,
                    filename=f"voice_reply.{ext}",
                    title="Voice Reply",
                )
            except Exception:
                log.warning("slack.audio_upload_failed", channel=message.recipient_id)

        # Always send text
        await self._app.client.chat_postMessage(
            channel=message.recipient_id,
            text=message.text,
        )
