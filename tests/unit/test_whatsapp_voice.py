from __future__ import annotations

import asyncio
import base64
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from jarvis.channels.base import ChannelType, OutboundMessage


class FakeResponse:
    """Minimal mock for aiohttp response in async context manager."""

    def __init__(self):
        self.status = 200

    def raise_for_status(self):
        pass

    async def json(self):
        return {"status": "sent", "audio_id": "test", "text_id": "test"}


class FakeSession:
    """Mock aiohttp session that tracks calls."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self._ctx()

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self._ctx()

    @asynccontextmanager
    async def _ctx(self):
        yield FakeResponse()


@pytest.fixture()
def whatsapp_channel():
    from jarvis.channels.whatsapp import WhatsAppChannel

    ch = WhatsAppChannel(bridge_url="http://localhost:9120")
    ch._session = FakeSession()
    ch._on_message = AsyncMock()
    return ch


class TestWhatsAppVoiceDispatch:
    def test_dispatch_webhook_audio_message(self, whatsapp_channel):
        data = {
            "sender": "123@s.whatsapp.net",
            "chat_jid": "123@s.whatsapp.net",
            "push_name": "Kartik",
            "text": "",
            "is_group": False,
            "is_status": False,
            "audio_data": base64.b64encode(b"fake-ogg-audio").decode(),
            "audio_mime": "audio/ogg; codecs=opus",
        }

        asyncio.run(whatsapp_channel.dispatch_webhook(data))

        whatsapp_channel._on_message.assert_called_once()
        msg = whatsapp_channel._on_message.call_args[0][0]
        assert msg.audio_data == b"fake-ogg-audio"
        assert msg.audio_mime == "audio/ogg; codecs=opus"
        assert msg.channel_type == ChannelType.WHATSAPP

    def test_audio_message_not_skipped(self, whatsapp_channel):
        """Audio-only messages (no text) should NOT be skipped."""
        data = {
            "sender": "123@s.whatsapp.net",
            "chat_jid": "123@s.whatsapp.net",
            "push_name": "Kartik",
            "text": "",
            "is_group": False,
            "is_status": False,
            "audio_data": base64.b64encode(b"audio").decode(),
            "audio_mime": "audio/ogg",
        }

        asyncio.run(whatsapp_channel.dispatch_webhook(data))

        whatsapp_channel._on_message.assert_called_once()

    def test_skip_when_no_text_and_no_audio(self, whatsapp_channel):
        """Messages with neither text nor audio should be skipped."""
        data = {
            "sender": "123@s.whatsapp.net",
            "chat_jid": "123@s.whatsapp.net",
            "push_name": "Kartik",
            "text": "",
            "is_group": False,
            "is_status": False,
        }

        asyncio.run(whatsapp_channel.dispatch_webhook(data))

        whatsapp_channel._on_message.assert_not_called()


class TestWhatsAppVoiceSend:
    def test_send_with_audio_calls_send_audio_endpoint(self, whatsapp_channel):
        msg = OutboundMessage(
            channel_type=ChannelType.WHATSAPP,
            recipient_id="123@s.whatsapp.net",
            text="Hello!",
            audio_data=b"mp3-bytes",
            audio_mime="audio/mp3",
        )
        asyncio.run(whatsapp_channel.send(msg))

        urls = [url for url, _ in whatsapp_channel._session.calls]
        assert any("/send-audio" in url for url in urls)

    def test_send_text_only_uses_regular_endpoint(self, whatsapp_channel):
        msg = OutboundMessage(
            channel_type=ChannelType.WHATSAPP,
            recipient_id="123@s.whatsapp.net",
            text="Hello!",
        )
        asyncio.run(whatsapp_channel.send(msg))

        urls = [url for url, _ in whatsapp_channel._session.calls]
        assert any(url.endswith("/send") for url in urls)
        assert not any("/send-audio" in url for url in urls)
