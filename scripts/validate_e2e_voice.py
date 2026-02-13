"""Phase 10 E2E validation — full voice pipeline with Letta agent.

Usage:
  # Voice round-trip (record mic -> STT -> Letta -> TTS -> play):
  uv run python scripts/validate_e2e_voice.py voice

  # Text round-trip with TTS (type text -> Letta -> TTS -> play):
  uv run python scripts/validate_e2e_voice.py text "what is the weather like?"
"""
import asyncio
import io
import os
import sys
import time

api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    sys.exit(1)

import numpy as np
import sounddevice as sd
import soundfile as sf
from letta_client import Letta

from jarvis.agent.factory import get_or_create_agent
from jarvis.channels.base import (
    ChannelMessage,
    ChannelType,
    ChannelUser,
    OutboundMessage,
)
from jarvis.channels.router import MessageRouter
from jarvis.settings import load_settings
from jarvis.voice.service import VoiceService

SAMPLE_RATE = 16000
RECORD_SECONDS = 5


def record_audio() -> bytes:
    print(f"RECORDING for {RECORD_SECONDS}s... SPEAK NOW!")
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    print("Recording complete.")
    peak = np.abs(audio).max()
    print(f"Peak amplitude: {peak:.4f}")
    buf = io.BytesIO()
    sf.write(buf, audio, SAMPLE_RATE, format="WAV")
    return buf.getvalue()


def play_audio(audio_bytes: bytes):
    buf = io.BytesIO(audio_bytes)
    data, samplerate = sf.read(buf)
    print("Playing audio response...")
    sd.play(data, samplerate)
    sd.wait()
    print("Playback complete.")


class CaptureChannel:
    def __init__(self):
        self.last_message = None

    @property
    def channel_type(self):
        return ChannelType.CLI

    async def send(self, message: OutboundMessage):
        self.last_message = message
        print(f"\nJarvis: {message.text}")
        if message.audio_data:
            print(
                f"[Audio: {len(message.audio_data)} bytes,"
                f" {message.audio_mime}]"
            )


async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "voice"
    text_input = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    print("=== Phase 10 E2E Voice Test ===\n")

    settings = load_settings()
    client = Letta(base_url=settings.letta.base_url)
    agent, tool_count = get_or_create_agent(client, settings)
    print(f"Agent: {agent.name} (tools={tool_count})")

    voice = VoiceService(api_key=api_key)
    capture = CaptureChannel()
    router = MessageRouter(
        client=client,
        agent_id=agent.id,
        channels={ChannelType.CLI: capture},
        voice_service=voice,
        tts_mode="always",
    )
    print("Router ready (tts_mode=always)\n")

    if mode == "voice":
        # 3s countdown then record
        print("Starting in 3s...")
        time.sleep(3)
        wav_bytes = record_audio()

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(
                id="cli-user", display_name=settings.user.name
            ),
            text="",
            audio_data=wav_bytes,
            audio_mime="audio/wav",
        )
        print("\nProcessing: STT -> Letta -> TTS...")
        await router.handle_inbound(msg)

    elif mode == "text":
        if not text_input:
            text_input = "Hello Jarvis, how are you?"
        print(f'Sending text: "{text_input}"')
        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(
                id="cli-user", display_name=settings.user.name
            ),
            text=text_input,
        )
        print("Processing: Letta -> TTS...")
        await router.handle_inbound(msg)

    if capture.last_message and capture.last_message.audio_data:
        play_audio(capture.last_message.audio_data)
        print("\nPASSED")
    else:
        print("\nWARN: No audio in response")


if __name__ == "__main__":
    asyncio.run(main())
