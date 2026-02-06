from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp


class TestWhatsAppChannel:
    def test_channel_type(self):
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")
        assert ch.channel_type.value == "whatsapp"

    async def test_start_stores_callback(self):
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")
        handler = AsyncMock()

        with patch.object(ch, "_check_bridge_health", new_callable=AsyncMock):
            await ch.start(handler)

        assert ch._on_message is handler
        assert ch._session is not None
        await ch.stop()

    async def test_send_posts_to_bridge(self):
        from jarvis.channels.base import ChannelType, OutboundMessage
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")

        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_session.post = MagicMock(return_value=mock_resp)
        ch._session = mock_session

        outbound = OutboundMessage(
            channel_type=ChannelType.WHATSAPP,
            recipient_id="919876543210@s.whatsapp.net",
            text="Hello from Jarvis",
        )

        await ch.send(outbound)

        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "http://localhost:9120/send"
        assert call_args[1]["json"]["to"] == "919876543210@s.whatsapp.net"
        assert call_args[1]["json"]["text"] == "Hello from Jarvis"

    async def test_send_retries_on_failure(self):
        from jarvis.channels.base import ChannelType, OutboundMessage
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")

        # First call fails, second succeeds
        fail_resp = AsyncMock()
        fail_resp.raise_for_status = MagicMock(side_effect=aiohttp.ClientError())
        fail_resp.__aenter__ = AsyncMock(return_value=fail_resp)
        fail_resp.__aexit__ = AsyncMock(return_value=False)

        ok_resp = AsyncMock()
        ok_resp.raise_for_status = MagicMock()
        ok_resp.__aenter__ = AsyncMock(return_value=ok_resp)
        ok_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_session.post = MagicMock(side_effect=[fail_resp, ok_resp])
        ch._session = mock_session

        outbound = OutboundMessage(
            channel_type=ChannelType.WHATSAPP,
            recipient_id="919876543210@s.whatsapp.net",
            text="Retry test",
        )

        with patch("jarvis.channels.whatsapp.asyncio.sleep", new_callable=AsyncMock):
            await ch.send(outbound)

        assert mock_session.post.call_count == 2

    async def test_dispatch_webhook_normalizes_message(self):
        from jarvis.channels.base import ChannelType
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")
        handler = AsyncMock()
        ch._on_message = handler

        data = {
            "sender": "919876543210@s.whatsapp.net",
            "chat_jid": "919876543210@s.whatsapp.net",
            "push_name": "Kartik",
            "text": "hello jarvis",
            "is_group": False,
            "is_status": False,
        }

        await ch.dispatch_webhook(data)

        handler.assert_called_once()
        msg = handler.call_args[0][0]
        assert msg.channel_type == ChannelType.WHATSAPP
        assert msg.user.id == "919876543210@s.whatsapp.net"
        assert msg.user.display_name == "Kartik"
        assert msg.text == "hello jarvis"

    def test_should_skip_empty_text(self):
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")
        assert ch._should_skip({"text": "", "is_group": False, "is_status": False}) is True
        assert ch._should_skip({"is_group": False, "is_status": False}) is True

    def test_should_skip_group_messages(self):
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")
        data = {"text": "hello", "is_group": True, "is_status": False}
        assert ch._should_skip(data) is True

    def test_does_not_skip_valid_dm(self):
        from jarvis.channels.whatsapp import WhatsAppChannel

        ch = WhatsAppChannel(bridge_url="http://localhost:9120")
        data = {"text": "hello", "is_group": False, "is_status": False}
        assert ch._should_skip(data) is False
