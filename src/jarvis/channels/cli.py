from __future__ import annotations

import asyncio
import io

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

# Lazy imports — only loaded when voice is actually used
sd = None  # sounddevice
sf = None  # soundfile (from scipy/soundfile)


def _ensure_audio_libs() -> bool:
    """Lazy-import audio libraries. Returns True if available, False otherwise."""
    global sd, sf
    if sd is not None:
        return True
    try:
        import sounddevice as _sd
        import soundfile as _sf
        sd = _sd
        sf = _sf
        return True
    except OSError:
        # PortAudio or libsndfile not installed (e.g. Docker container)
        log.warning("cli.audio_libs_unavailable", reason="PortAudio/libsndfile not found")
        return False


_SAMPLE_RATE = 16000
_RECORD_SECONDS = 5


class CLIChannel(Channel):
    """Dev/testing channel using stdin/stdout."""

    def __init__(self, user_name: str = "User", voice_enabled: bool = False) -> None:
        self._user_name = user_name
        self._running = False
        self._voice_enabled = voice_enabled

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.CLI

    async def start(self, on_message: InboundHandler) -> None:
        """Read lines from stdin, dispatch as messages."""
        self._running = True
        user = ChannelUser(id="cli-user", display_name=self._user_name)

        if self._voice_enabled and not _ensure_audio_libs():
            log.warning("cli.voice_disabled", reason="audio libs unavailable")
            self._voice_enabled = False

        log.info("cli.started", voice=self._voice_enabled)
        while self._running:
            try:
                if self._voice_enabled:
                    line = await asyncio.to_thread(
                        input, "[Press Enter to record, or type text] "
                    )
                else:
                    line = await asyncio.to_thread(input, "You: ")
            except EOFError:
                break

            stripped = line.strip()
            if stripped.lower() in ("quit", "exit"):
                break

            if self._voice_enabled and not stripped:
                # Record audio
                print(f"Recording for {_RECORD_SECONDS}s...")
                audio_data = await asyncio.to_thread(self._record_audio)
                print("Recording complete.")
                msg = ChannelMessage(
                    channel_type=ChannelType.CLI,
                    user=user,
                    text="",
                    audio_data=audio_data,
                    audio_mime="audio/wav",
                )
            elif stripped:
                msg = ChannelMessage(
                    channel_type=ChannelType.CLI, user=user, text=stripped
                )
            else:
                continue

            await on_message(msg)

        self._running = False
        log.info("cli.stopped")

    async def stop(self) -> None:
        self._running = False

    async def send(self, message: OutboundMessage) -> None:
        print(f"Jarvis: {message.text}")
        if message.audio_data and self._voice_enabled:
            self._play_audio(message.audio_data)

    def _record_audio(self) -> bytes:
        """Record audio from microphone, return WAV bytes."""
        _ensure_audio_libs()
        audio = sd.rec(
            int(_RECORD_SECONDS * _SAMPLE_RATE),
            samplerate=_SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        buf = io.BytesIO()
        sf.write(buf, audio, _SAMPLE_RATE, format="WAV")
        return buf.getvalue()

    def _play_audio(self, audio_data: bytes) -> None:
        """Play audio bytes through speakers."""
        _ensure_audio_libs()
        buf = io.BytesIO(audio_data)
        data, samplerate = sf.read(buf)
        sd.play(data, samplerate)
        sd.wait()
