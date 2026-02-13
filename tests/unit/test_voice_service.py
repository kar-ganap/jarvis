from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestVoiceServiceInit:
    def test_creates_openai_client(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI") as mock_openai:
            svc = VoiceService(api_key="sk-test")
            mock_openai.assert_called_once_with(api_key="sk-test")
            assert svc._stt_model == "whisper-1"
            assert svc._tts_model == "tts-1"
            assert svc._tts_voice == "nova"

    def test_custom_models(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI"):
            svc = VoiceService(
                api_key="sk-test",
                stt_model="whisper-2",
                tts_model="tts-1-hd",
                tts_voice="alloy",
            )
            assert svc._stt_model == "whisper-2"
            assert svc._tts_model == "tts-1-hd"
            assert svc._tts_voice == "alloy"


class TestMimeToExtension:
    def test_ogg(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/ogg") == ".ogg"

    def test_ogg_with_codecs(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/ogg; codecs=opus") == ".ogg"

    def test_mp3(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/mpeg") == ".mp3"

    def test_wav(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/wav") == ".wav"

    def test_m4a(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/mp4") == ".m4a"

    def test_webm(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/webm") == ".webm"

    def test_unknown_defaults_to_ogg(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("audio/unknown") == ".ogg"

    def test_video_mp4(self):
        from jarvis.voice.service import _mime_to_extension

        assert _mime_to_extension("video/mp4") == ".mp4"


class TestTranscribe:
    def test_calls_openai_api(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = MagicMock(
                text="hello world"
            )

            svc = VoiceService(api_key="sk-test")
            result = svc.transcribe(b"fake-audio-bytes", "audio/ogg")

            assert result == "hello world"
            mock_client.audio.transcriptions.create.assert_called_once()
            call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
            assert call_kwargs["model"] == "whisper-1"

    def test_returns_text(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = MagicMock(
                text="transcribed speech"
            )

            svc = VoiceService(api_key="sk-test")
            result = svc.transcribe(b"\x00\x01\x02", "audio/mpeg")

            assert isinstance(result, str)
            assert result == "transcribed speech"

    def test_empty_audio_raises(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI"):
            svc = VoiceService(api_key="sk-test")

            with pytest.raises(ValueError, match="empty"):
                svc.transcribe(b"", "audio/ogg")


class TestSynthesize:
    def test_calls_openai_tts(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = b"fake-mp3-bytes"
            mock_client.audio.speech.create.return_value = mock_response

            svc = VoiceService(api_key="sk-test")
            result = svc.synthesize("hello world")

            assert result == b"fake-mp3-bytes"
            mock_client.audio.speech.create.assert_called_once()
            call_kwargs = mock_client.audio.speech.create.call_args[1]
            assert call_kwargs["model"] == "tts-1"
            assert call_kwargs["voice"] == "nova"
            assert call_kwargs["input"] == "hello world"
            assert call_kwargs["response_format"] == "opus"

    def test_returns_bytes(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = b"\xff\xfb\x90"
            mock_client.audio.speech.create.return_value = mock_response

            svc = VoiceService(api_key="sk-test")
            result = svc.synthesize("test")

            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_empty_text_returns_empty(self):
        from jarvis.voice.service import VoiceService

        with patch("jarvis.voice.service.openai.OpenAI"):
            svc = VoiceService(api_key="sk-test")
            result = svc.synthesize("")

            assert result == b""
