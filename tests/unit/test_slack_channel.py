from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock


class TestSlackChannel:
    def test_channel_type(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")
        assert ch.channel_type.value == "slack"

    async def test_normalizes_message_event(self):
        from jarvis.channels.base import ChannelType
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")
        handler = AsyncMock()
        ch._on_message = handler

        mock_client = AsyncMock()
        mock_client.users_info.return_value = {
            "user": {
                "profile": {
                    "display_name": "Kartik",
                    "real_name": "Kartik G",
                }
            }
        }

        event = {
            "user": "U123",
            "text": "hello jarvis",
            "channel": "D456",
            "ts": "123.456",
        }

        await ch._dispatch(event, mock_client)

        handler.assert_called_once()
        msg = handler.call_args[0][0]
        assert msg.channel_type == ChannelType.SLACK
        assert msg.user.id == "D456"
        assert msg.user.display_name == "Kartik"
        assert msg.text == "hello jarvis"

    async def test_normalizes_mention_event(self):
        from jarvis.channels.base import ChannelType
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")
        handler = AsyncMock()
        ch._on_message = handler

        mock_client = AsyncMock()
        mock_client.users_info.return_value = {
            "user": {
                "profile": {
                    "display_name": "Kartik",
                    "real_name": "Kartik G",
                }
            }
        }

        event = {
            "user": "U123",
            "text": "<@B789> what time is it?",
            "channel": "C999",
            "ts": "789.012",
        }

        await ch._dispatch(event, mock_client)

        handler.assert_called_once()
        msg = handler.call_args[0][0]
        assert msg.channel_type == ChannelType.SLACK
        assert msg.user.id == "C999"
        assert msg.text == "<@B789> what time is it?"

    async def test_filters_bot_messages(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")
        handler = AsyncMock()
        ch._on_message = handler

        # Event with bot_id — should be filtered
        event = {
            "user": "U123",
            "text": "I am a bot",
            "channel": "D456",
            "bot_id": "B999",
        }

        # _dispatch shouldn't be called for bot messages,
        # but the filtering happens in the listener, not _dispatch.
        # So we test that the channel skips bot_id in _should_skip.
        assert ch._should_skip(event) is True

    async def test_filters_bot_subtype_messages(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")

        event = {
            "user": "U123",
            "text": "bot reply",
            "channel": "D456",
            "subtype": "bot_message",
        }
        assert ch._should_skip(event) is True

    async def test_does_not_skip_user_messages(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")

        event = {
            "user": "U123",
            "text": "hello",
            "channel": "D456",
        }
        assert ch._should_skip(event) is False

    async def test_does_not_skip_file_share(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")

        event = {
            "user": "U123",
            "text": "",
            "channel": "D456",
            "subtype": "file_share",
            "files": [{"mimetype": "audio/webm"}],
        }
        assert ch._should_skip(event) is False

    async def test_skips_other_subtypes(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")

        for subtype in ("channel_join", "channel_leave", "thread_broadcast"):
            event = {
                "user": "U123",
                "text": "",
                "channel": "D456",
                "subtype": subtype,
            }
            assert ch._should_skip(event) is True

    async def test_send_calls_chat_post_message(self):
        from jarvis.channels.base import ChannelType, OutboundMessage
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")
        ch._app = MagicMock()
        ch._app.client.chat_postMessage = AsyncMock()

        outbound = OutboundMessage(
            channel_type=ChannelType.SLACK,
            recipient_id="C123",
            text="Hello from Jarvis",
        )

        await ch.send(outbound)

        ch._app.client.chat_postMessage.assert_called_once_with(
            channel="C123",
            text="Hello from Jarvis",
        )

    async def test_resolve_user_name_fallback(self):
        from jarvis.channels.slack import SlackChannel

        ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")

        mock_client = AsyncMock()
        mock_client.users_info.side_effect = Exception("API error")

        name = await ch._resolve_user_name(mock_client, "U123")
        assert name == "User"
