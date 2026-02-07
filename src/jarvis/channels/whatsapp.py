from __future__ import annotations

import asyncio

import aiohttp
import structlog

from jarvis.channels.base import (
    Channel,
    ChannelMessage,
    ChannelType,
    ChannelUser,
    InboundHandler,
    OutboundMessage,
)

log = structlog.get_logger()


class WhatsAppChannel(Channel):
    """WhatsApp channel via Node.js Baileys bridge."""

    def __init__(self, bridge_url: str, allow_groups: bool = False) -> None:
        self._bridge_url = bridge_url.rstrip("/")
        self._allow_groups = allow_groups
        self._on_message: InboundHandler | None = None
        self._session: aiohttp.ClientSession | None = None

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.WHATSAPP

    async def start(self, on_message: InboundHandler) -> None:
        """Store callback, create HTTP session, health-check bridge."""
        self._on_message = on_message
        self._session = aiohttp.ClientSession()
        await self._check_bridge_health()
        log.info("whatsapp.started", bridge_url=self._bridge_url)

    async def stop(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
        log.info("whatsapp.stopped")

    async def send(self, message: OutboundMessage) -> None:
        """Send a message via the Baileys bridge. Retries once on failure."""
        payload = {"to": message.recipient_id, "text": message.text}
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with self._session.post(
                f"{self._bridge_url}/send", json=payload, timeout=timeout,
            ) as resp:
                resp.raise_for_status()
        except (aiohttp.ClientError, TimeoutError):
            log.warning("whatsapp.send_failed_retrying", recipient=message.recipient_id)
            await asyncio.sleep(2)
            async with self._session.post(
                f"{self._bridge_url}/send", json=payload, timeout=timeout,
            ) as resp:
                resp.raise_for_status()

    async def dispatch_webhook(self, data: dict) -> None:
        """Normalize webhook payload to ChannelMessage and forward to router."""
        if self._should_skip(data):
            return

        sender = data.get("sender", "")
        push_name = data.get("push_name", "Unknown")
        text = data.get("text", "")
        user_id = data.get("chat_jid", sender)
        is_group = data.get("is_group", False)

        msg = ChannelMessage(
            channel_type=ChannelType.WHATSAPP,
            user=ChannelUser(id=user_id, display_name=push_name),
            text=text,
            raw=data,
        )

        log.info("whatsapp.inbound", sender=push_name, is_group=is_group)

        if self._on_message:
            await self._on_message(msg)

    def _should_skip(self, data: dict) -> bool:
        """Return True if this message should be ignored."""
        if not data.get("text"):
            return True
        if data.get("is_status", False):
            return True
        if data.get("is_group", False) and not self._allow_groups:
            return True
        return False

    async def _check_bridge_health(self) -> None:
        """Health-check the bridge. Logs warning if unreachable (non-fatal)."""
        try:
            async with self._session.get(
                f"{self._bridge_url}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                info = await resp.json()
                log.info("whatsapp.bridge_health", connected=info.get("connected"))
        except Exception:
            log.warning("whatsapp.bridge_unreachable", bridge_url=self._bridge_url)
