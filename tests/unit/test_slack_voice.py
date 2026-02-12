from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from jarvis.channels.base import ChannelType, OutboundMessage


@pytest.fixture()
def slack_channel():
    from jarvis.channels.slack import SlackChannel

    ch = SlackChannel(bot_token="xoxb-test", app_token="xapp-test")
    ch._on_message = AsyncMock()
    ch._app = MagicMock()
    ch._app.client = AsyncMock()
    return ch


class TestSlackVoiceDispatch:
    def test_dispatch_audio_file_message(self, slack_channel):
        """Slack message with an audio file attachment should extract audio."""
        mock_client = AsyncMock()
        # Mock file download
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "Kartik"}}
        }

        event = {
            "user": "U123",
            "channel": "C456",
            "text": "",
            "files": [
                {
                    "mimetype": "audio/webm",
                    "url_private_download": "https://files.slack.com/audio.webm",
                    "size": 1024,
                }
            ],
        }

        # We need to test _dispatch directly, mocking the file download
        from unittest.mock import patch


        async def mock_read():
            return b"fake-audio-bytes"

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read = mock_read

        with patch.object(slack_channel, "_download_slack_file", return_value=b"fake-audio-bytes"):
            asyncio.run(slack_channel._dispatch(event, mock_client))

        slack_channel._on_message.assert_called_once()
        msg = slack_channel._on_message.call_args[0][0]
        assert msg.audio_data == b"fake-audio-bytes"
        assert msg.audio_mime == "audio/webm"

    def test_dispatch_text_only_no_audio(self, slack_channel):
        """Text-only messages should have no audio data."""
        mock_client = AsyncMock()
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "Kartik"}}
        }

        event = {
            "user": "U123",
            "channel": "C456",
            "text": "hello",
        }

        asyncio.run(slack_channel._dispatch(event, mock_client))

        slack_channel._on_message.assert_called_once()
        msg = slack_channel._on_message.call_args[0][0]
        assert msg.audio_data is None

    def test_non_audio_file_ignored(self, slack_channel):
        """Non-audio file attachments should not be treated as audio."""
        mock_client = AsyncMock()
        mock_client.users_info.return_value = {
            "user": {"profile": {"display_name": "Kartik"}}
        }

        event = {
            "user": "U123",
            "channel": "C456",
            "text": "check this image",
            "files": [
                {
                    "mimetype": "image/png",
                    "url_private_download": "https://files.slack.com/img.png",
                    "size": 2048,
                }
            ],
        }

        asyncio.run(slack_channel._dispatch(event, mock_client))

        msg = slack_channel._on_message.call_args[0][0]
        assert msg.audio_data is None


class TestSlackVoiceSend:
    def test_send_with_audio_uploads_file(self, slack_channel):
        """Outbound message with audio should upload a file."""
        msg = OutboundMessage(
            channel_type=ChannelType.SLACK,
            recipient_id="C456",
            text="Here's my reply",
            audio_data=b"mp3-bytes",
            audio_mime="audio/mp3",
        )
        asyncio.run(slack_channel.send(msg))

        # Should have called files_upload_v2 for audio
        slack_channel._app.client.files_upload_v2.assert_called_once()
        # Should also post text
        slack_channel._app.client.chat_postMessage.assert_called_once()

    def test_send_text_only_no_upload(self, slack_channel):
        """Text-only outbound should NOT upload a file."""
        msg = OutboundMessage(
            channel_type=ChannelType.SLACK,
            recipient_id="C456",
            text="Just text",
        )
        asyncio.run(slack_channel.send(msg))

        slack_channel._app.client.chat_postMessage.assert_called_once()
        slack_channel._app.client.files_upload_v2.assert_not_called()
