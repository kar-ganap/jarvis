from __future__ import annotations

import asyncio

import structlog

from jarvis.agent.response import extract_assistant_text, extract_tool_calls
from jarvis.channels.base import (
    Channel,
    ChannelMessage,
    ChannelType,
    OutboundMessage,
)
from jarvis.monitoring.metrics import MESSAGE_COUNT, TOOL_INVOCATION_COUNT

log = structlog.get_logger()


class MessageRouter:
    """Central hub connecting channels to the Letta agent."""

    def __init__(
        self,
        client,
        agent_id: str,
        channels: dict[ChannelType, Channel],
        voice_service=None,
        tts_mode: str = "auto",
    ) -> None:
        self._client = client
        self._agent_id = agent_id
        self._channels = channels
        self._voice = voice_service
        self._tts_mode = tts_mode
        self._lock = asyncio.Lock()

    async def handle_inbound(self, message: ChannelMessage) -> None:
        """Process an inbound message: format, send to Letta, reply to channel."""
        chan = message.channel_type
        uid = message.user.id
        name = message.user.display_name
        inbound_was_voice = False

        # STT: transcribe audio if present
        text = message.text
        if message.audio_data and self._voice:
            text = await asyncio.to_thread(
                self._voice.transcribe, message.audio_data, message.audio_mime or "audio/ogg",
            )
            inbound_was_voice = True
            log.info("router.transcribed", channel=chan, text_len=len(text))

        if not text:
            log.debug("router.no_text_after_transcription")
            return

        prefixed = f"[{chan}|{uid}|{name}] {text}"

        MESSAGE_COUNT.labels(channel=str(chan), direction="inbound").inc()

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

        for tc in extract_tool_calls(response):
            TOOL_INVOCATION_COUNT.labels(tool_name=tc["tool_name"]).inc()

        reply_text = extract_assistant_text(response)
        if not reply_text:
            log.debug("router.no_assistant_reply")
            return

        # TTS: synthesize audio if configured
        audio_data = None
        audio_mime = None
        if self._voice and self._should_synthesize(inbound_was_voice):
            audio_data = await asyncio.to_thread(self._voice.synthesize, reply_text)
            audio_mime = "audio/ogg; codecs=opus"

        outbound = OutboundMessage(
            channel_type=message.channel_type,
            recipient_id=message.user.id,
            text=reply_text,
            audio_data=audio_data,
            audio_mime=audio_mime,
        )

        channel = self._channels.get(message.channel_type)
        if channel:
            await channel.send(outbound)
            MESSAGE_COUNT.labels(
                channel=str(message.channel_type), direction="outbound",
            ).inc()

    def _should_synthesize(self, inbound_was_voice: bool) -> bool:
        """Decide whether to synthesize TTS based on tts_mode."""
        if self._tts_mode == "always":
            return True
        if self._tts_mode == "auto" and inbound_was_voice:
            return True
        return False

    async def send_proactive(
        self, channel_type: ChannelType, recipient_id: str, text: str
    ) -> None:
        """Send a proactive (agent-initiated) message to a channel."""
        audio_data = None
        audio_mime = None
        if self._voice and self._tts_mode == "always":
            audio_data = await asyncio.to_thread(self._voice.synthesize, text)
            audio_mime = "audio/ogg; codecs=opus"

        outbound = OutboundMessage(
            channel_type=channel_type,
            recipient_id=recipient_id,
            text=text,
            audio_data=audio_data,
            audio_mime=audio_mime,
        )
        channel = self._channels.get(channel_type)
        if channel:
            await channel.send(outbound)
            MESSAGE_COUNT.labels(
                channel=str(channel_type), direction="outbound",
            ).inc()
