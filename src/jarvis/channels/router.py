from __future__ import annotations

import asyncio

import structlog

from jarvis.agent.response import extract_assistant_text
from jarvis.channels.base import (
    Channel,
    ChannelMessage,
    ChannelType,
    OutboundMessage,
)

log = structlog.get_logger()


class MessageRouter:
    """Central hub connecting channels to the Letta agent."""

    def __init__(
        self,
        client,
        agent_id: str,
        channels: dict[ChannelType, Channel],
    ) -> None:
        self._client = client
        self._agent_id = agent_id
        self._channels = channels
        self._lock = asyncio.Lock()

    async def handle_inbound(self, message: ChannelMessage) -> None:
        """Process an inbound message: format, send to Letta, reply to channel."""
        prefixed = f"[{message.channel_type}|{message.user.display_name}] {message.text}"

        log.info(
            "router.inbound",
            channel=message.channel_type,
            user=message.user.display_name,
        )

        async with self._lock:
            response = await asyncio.to_thread(
                self._client.agents.messages.create,
                agent_id=self._agent_id,
                messages=[{"role": "user", "content": prefixed}],
            )

        reply_text = extract_assistant_text(response)
        if not reply_text:
            log.debug("router.no_assistant_reply")
            return

        outbound = OutboundMessage(
            channel_type=message.channel_type,
            recipient_id=message.user.id,
            text=reply_text,
        )

        channel = self._channels.get(message.channel_type)
        if channel:
            await channel.send(outbound)

    async def send_proactive(
        self, channel_type: ChannelType, recipient_id: str, text: str
    ) -> None:
        """Send a proactive (agent-initiated) message to a channel."""
        outbound = OutboundMessage(
            channel_type=channel_type, recipient_id=recipient_id, text=text
        )
        channel = self._channels.get(channel_type)
        if channel:
            await channel.send(outbound)
