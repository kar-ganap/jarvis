# Phase 10 Retrospective — Voice STT/TTS

## Delivered

### VoiceService Core
- `VoiceService` class wrapping OpenAI Whisper (STT) and TTS (tts-1) APIs
- `_mime_to_extension()` mapping for audio format detection
- Streaming TTS support via `synthesize_streaming()`
- `VoiceSettings` with configurable models, voice, and tts_mode

### Message Model Extension
- Optional `audio_data: bytes | None` and `audio_mime: str | None` on `ChannelMessage` and `OutboundMessage`
- Fully backward-compatible — existing code unaffected

### Router Integration
- `MessageRouter` accepts optional `VoiceService` and `tts_mode`
- Inbound: auto-transcribes audio messages via STT
- Outbound: auto-synthesizes replies via TTS based on tts_mode
- `send_proactive` also gets TTS when tts_mode="always"
- STT/TTS runs outside Letta lock to avoid blocking

### WhatsApp Voice
- Bridge captures `audioMessage` via Baileys `downloadMediaMessage()`
- Base64-encoded audio in webhook payload
- New `/send-audio` bridge endpoint sends voice notes (`ptt: true`)
- `_should_skip` allows audio-only messages (no text required)
- JSON body limit raised to 10MB for audio payloads

### Slack Voice
- Audio file detection from `event.files` (mimetype starts with `audio/`)
- File download via `url_private_download` with bot token auth
- Audio reply upload via `files_upload_v2`
- Text reply always sent alongside audio

### CLI Voice I/O
- Full voice I/O: mic recording via `sounddevice.rec()` + audio playback via `sounddevice.play()`
- Press Enter to record (5s fixed duration), or type text normally
- Lazy imports for `sounddevice`/`soundfile` — only loaded when voice enabled
- WAV format for recording, MP3 from TTS playback

## Numbers

| Metric | Phase 9 | Phase 10 | Delta |
|--------|---------|----------|-------|
| Letta tools | 44 | 44 | +0 |
| HTTP endpoints | 42 | 42 | +0 |
| Unit tests | 218 | 262 | +44 |
| Integration tests | 16 | 16 | +0 |
| Total tests | 234 | 278 | +44 |

## What Went Well

- **Voice as transparent layer**: Agent never knows about audio. Clean separation of concerns — all voice logic lives in infrastructure (VoiceService + router + channels).
- **TDD rhythm**: RED → GREEN cycle worked cleanly for all 7 sub-phases.
- **Backward compatibility**: Adding optional fields to frozen dataclasses with `None` defaults required zero changes to existing tests.
- **Lazy imports**: `sounddevice` and `soundfile` are only imported when voice is enabled, so CLI works without PortAudio installed.
- **tts_mode flexibility**: "auto" (only for voice input), "always" (every reply), "never" (text only) — covers all use cases.

## What Could Be Better

- **CLI recording is fixed duration**: 5 seconds, no silence detection. A VAD (voice activity detection) approach would be more natural.
- **No streaming playback**: TTS response is fully buffered before playback. Could stream chunks for lower perceived latency.
- **WhatsApp audio is base64 in JSON**: Could use multipart form for better efficiency, but JSON keeps it simple.

## Gotchas Discovered

- **OpenAI Whisper needs file extension**: `transcriptions.create()` infers audio format from the filename extension. Must use correct extension (`.ogg`, `.mp3`, etc.).
- **Baileys `downloadMediaMessage`**: Requires the full `msg` object, not just the audio field. Returns a Buffer.
- **`express.json()` 100KB limit**: Default body size limit breaks base64 audio payloads. Must set `{ limit: '10mb' }`.
- **aiohttp mock for tests**: `AsyncMock()` session doesn't properly mock async context managers for `session.post()`. Used custom `FakeSession` class instead.
- **sounddevice needs PortAudio**: System dependency — `brew install portaudio` on macOS. Not a Python package issue.
