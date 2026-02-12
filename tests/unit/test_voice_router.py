from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from jarvis.channels.base import (
    ChannelMessage,
    ChannelType,
    ChannelUser,
)


def _make_letta_response(text="Hello back!"):
    response = MagicMock()
    msg = MagicMock()
    msg.message_type = "assistant_message"
    msg.content = text
    response.messages = [msg]
    return response


def _make_router(voice_service=None, tts_mode="auto"):
    from jarvis.channels.router import MessageRouter

    mock_client = MagicMock()
    mock_client.agents.messages.create.return_value = _make_letta_response()

    mock_channel = AsyncMock()
    channels = {ChannelType.CLI: mock_channel}

    router = MessageRouter(
        client=mock_client,
        agent_id="agent-1",
        channels=channels,
        voice_service=voice_service,
        tts_mode=tts_mode,
    )
    return router, mock_channel, mock_client


def _make_user():
    return ChannelUser(id="cli-user", display_name="Kartik")


@pytest.mark.asyncio
class TestRouterVoiceTranscribe:
    async def test_inbound_audio_message_transcribed(self):
        mock_voice = MagicMock()
        mock_voice.transcribe.return_value = "transcribed text"
        router, mock_channel, _ = _make_router(voice_service=mock_voice)

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="",
            audio_data=b"fake-audio",
            audio_mime="audio/ogg",
        )
        await router.handle_inbound(msg)

        mock_voice.transcribe.assert_called_once_with(b"fake-audio", "audio/ogg")

    async def test_inbound_text_message_not_transcribed(self):
        mock_voice = MagicMock()
        router, mock_channel, _ = _make_router(voice_service=mock_voice)

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="hello",
        )
        await router.handle_inbound(msg)

        mock_voice.transcribe.assert_not_called()

    async def test_transcription_text_used_as_message_text(self):
        mock_voice = MagicMock()
        mock_voice.transcribe.return_value = "what is the weather"
        router, _, mock_client = _make_router(voice_service=mock_voice)

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="",
            audio_data=b"audio-bytes",
            audio_mime="audio/ogg",
        )
        await router.handle_inbound(msg)

        call_args = mock_client.agents.messages.create.call_args
        sent_content = call_args[1]["messages"][0]["content"]
        assert "what is the weather" in sent_content


@pytest.mark.asyncio
class TestRouterVoiceSynthesize:
    async def test_outbound_has_audio_when_voice_service_present_and_always(self):
        mock_voice = MagicMock()
        mock_voice.synthesize.return_value = b"mp3-bytes"
        router, mock_channel, _ = _make_router(
            voice_service=mock_voice, tts_mode="always"
        )

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="hello",
        )
        await router.handle_inbound(msg)

        mock_voice.synthesize.assert_called_once()
        sent_msg = mock_channel.send.call_args[0][0]
        assert sent_msg.audio_data == b"mp3-bytes"
        assert sent_msg.audio_mime == "audio/ogg; codecs=opus"

    async def test_outbound_no_audio_when_tts_mode_never(self):
        mock_voice = MagicMock()
        router, mock_channel, _ = _make_router(
            voice_service=mock_voice, tts_mode="never"
        )

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="hello",
        )
        await router.handle_inbound(msg)

        mock_voice.synthesize.assert_not_called()
        sent_msg = mock_channel.send.call_args[0][0]
        assert sent_msg.audio_data is None

    async def test_outbound_audio_only_on_voice_inbound_when_auto(self):
        mock_voice = MagicMock()
        mock_voice.transcribe.return_value = "voice input"
        mock_voice.synthesize.return_value = b"mp3-bytes"
        router, mock_channel, _ = _make_router(
            voice_service=mock_voice, tts_mode="auto"
        )

        # Text-only inbound — no TTS
        text_msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="hello",
        )
        await router.handle_inbound(text_msg)
        mock_voice.synthesize.assert_not_called()

        # Audio inbound — TTS
        audio_msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="",
            audio_data=b"audio",
            audio_mime="audio/ogg",
        )
        await router.handle_inbound(audio_msg)
        mock_voice.synthesize.assert_called_once()

    async def test_router_works_without_voice_service(self):
        router, mock_channel, _ = _make_router(voice_service=None)

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=_make_user(),
            text="hello",
        )
        await router.handle_inbound(msg)

        mock_channel.send.assert_called_once()
        sent_msg = mock_channel.send.call_args[0][0]
        assert sent_msg.audio_data is None

    async def test_proactive_message_gets_audio_when_always(self):
        mock_voice = MagicMock()
        mock_voice.synthesize.return_value = b"proactive-audio"
        router, mock_channel, _ = _make_router(
            voice_service=mock_voice, tts_mode="always"
        )

        await router.send_proactive(ChannelType.CLI, "cli-user", "reminder!")

        mock_voice.synthesize.assert_called_once_with("reminder!")
        sent_msg = mock_channel.send.call_args[0][0]
        assert sent_msg.audio_data == b"proactive-audio"
