"""Phase 10 live validation — CLI voice I/O (mic -> STT -> TTS -> speaker).

Usage:
  set -a && source ~/.zshrc && set +a
  uv run python scripts/validate_cli_voice.py
"""
import io
import os
import sys

api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    sys.exit(1)

import numpy as np
import sounddevice as sd
import soundfile as sf

from jarvis.voice.service import VoiceService

SAMPLE_RATE = 16000
RECORD_SECONDS = 5

svc = VoiceService(api_key=api_key)

print("=== CLI Voice I/O Test ===")
print(f"Will record {RECORD_SECONDS}s from your microphone.")
print("Speak after the 'Recording...' prompt.\n")

input("Press Enter to start recording...")

print(f"Recording for {RECORD_SECONDS}s...")
audio = sd.rec(
    int(RECORD_SECONDS * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
)
sd.wait()
print("Recording complete.\n")

# Convert to WAV bytes
buf = io.BytesIO()
sf.write(buf, audio, SAMPLE_RATE, format="WAV")
wav_bytes = buf.getvalue()
print(f"Recorded {len(wav_bytes)} bytes of WAV audio")

# Check if there's actual audio (not just silence)
peak = np.abs(audio).max()
print(f"Peak amplitude: {peak:.4f}")
if peak < 0.01:
    print(
        "WARNING: Very low audio level"
        " — mic might not be working or you were silent"
    )

# STT
print("\nTranscribing with Whisper...")
transcript = svc.transcribe(wav_bytes, "audio/wav")
print(f'You said: "{transcript}"')

if not transcript.strip():
    print("No speech detected. Exiting.")
    sys.exit(0)

# TTS reply
reply = f"I heard you say: {transcript}. That's interesting!"
print(f'\nGenerating TTS reply: "{reply}"')
reply_audio = svc.synthesize(reply)
print(f"TTS output: {len(reply_audio)} bytes of MP3")

# Play the reply
print("Playing reply...")
reply_buf = io.BytesIO(reply_audio)
data, samplerate = sf.read(reply_buf)
sd.play(data, samplerate)
sd.wait()
print("Done!")

print("\n=== CLI Voice I/O Test PASSED ===")
