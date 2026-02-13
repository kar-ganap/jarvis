from __future__ import annotations

from collections.abc import Iterator

import openai
import structlog

log = structlog.get_logger()

_MIME_EXTENSIONS: dict[str, str] = {
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/m4a": ".m4a",
    "audio/webm": ".webm",
    "audio/flac": ".flac",
    "video/mp4": ".mp4",
}


def _mime_to_extension(mime_type: str) -> str:
    """Map MIME type to file extension. Strips codec params."""
    base = mime_type.split(";")[0].strip()
    return _MIME_EXTENSIONS.get(base, ".ogg")


class VoiceService:
    """STT/TTS via OpenAI API."""

    def __init__(
        self,
        api_key: str,
        stt_model: str = "whisper-1",
        tts_model: str = "tts-1",
        tts_voice: str = "nova",
    ) -> None:
        self._client = openai.OpenAI(api_key=api_key)
        self._stt_model = stt_model
        self._tts_model = tts_model
        self._tts_voice = tts_voice

    def transcribe(self, audio_data: bytes, mime_type: str = "audio/ogg") -> str:
        """STT: audio bytes → text. Uses OpenAI Whisper."""
        if not audio_data:
            raise ValueError("Cannot transcribe empty audio data")

        ext = _mime_to_extension(mime_type)
        filename = f"audio{ext}"
        response = self._client.audio.transcriptions.create(
            model=self._stt_model,
            file=(filename, audio_data),
        )
        log.info("voice.transcribed", length=len(audio_data), mime=mime_type)
        return response.text

    def synthesize(self, text: str, response_format: str = "opus") -> bytes:
        """TTS: text → audio bytes. Uses OpenAI TTS.

        Default format is opus (OGG/Opus) for WhatsApp voice note compatibility.
        """
        if not text:
            return b""

        response = self._client.audio.speech.create(
            model=self._tts_model,
            voice=self._tts_voice,
            input=text,
            response_format=response_format,
        )
        audio = response.content
        log.info("voice.synthesized", text_len=len(text), audio_len=len(audio))
        return audio

    def synthesize_streaming(self, text: str) -> Iterator[bytes]:
        """TTS with streaming: yields opus chunks."""
        if not text:
            return

        response = self._client.audio.speech.create(
            model=self._tts_model,
            voice=self._tts_voice,
            input=text,
            response_format="opus",
        )
        yield from response.iter_bytes(chunk_size=4096)
