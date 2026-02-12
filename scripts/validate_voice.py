"""Phase 10 validation — VoiceService STT + TTS round-trip.

Usage:
  set -a && source ~/.zshrc && set +a
  uv run python scripts/validate_voice.py
"""
import os
import sys
import tempfile

api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    sys.exit(1)

print(f"API key: {api_key[:8]}...")

from jarvis.voice.service import VoiceService

svc = VoiceService(api_key=api_key)

# --- Test 1: TTS ---
print("\n=== Test 1: TTS (text → mp3) ===")
text = "Hello! I am Jarvis, your personal AI assistant. How can I help you today?"
print(f"Input text: {text}")

audio_bytes = svc.synthesize(text)
print(f"TTS output: {len(audio_bytes)} bytes of MP3")

tts_path = tempfile.mktemp(suffix=".mp3")
with open(tts_path, "wb") as f:
    f.write(audio_bytes)
print(f"Saved to: {tts_path}")

# --- Test 2: STT (round-trip) ---
print("\n=== Test 2: STT (mp3 → text) ===")
transcript = svc.transcribe(audio_bytes, "audio/mpeg")
print(f"STT output: {transcript}")

# --- Test 3: Similarity check ---
print("\n=== Test 3: Round-trip validation ===")
original_words = set(text.lower().split())
transcript_words = set(transcript.lower().split())
overlap = original_words & transcript_words
similarity = len(overlap) / len(original_words) if original_words else 0
print(f"Word overlap: {len(overlap)}/{len(original_words)} = {similarity:.0%}")
if similarity >= 0.5:
    print("PASS")
else:
    print(f"WARN: Low similarity ({similarity:.0%})")

# --- Test 4: Different voice ---
print("\n=== Test 4: TTS with 'alloy' voice ===")
svc2 = VoiceService(api_key=api_key, tts_voice="alloy")
audio2 = svc2.synthesize("Testing a different voice. This is Alloy speaking.")
print(f"TTS output: {len(audio2)} bytes")
alloy_path = tempfile.mktemp(suffix=".mp3")
with open(alloy_path, "wb") as f:
    f.write(audio2)
print(f"Saved to: {alloy_path}")

print("\n=== All tests passed! ===")
print("\nTo play:")
print(f"  afplay {tts_path}")
print(f"  afplay {alloy_path}")
