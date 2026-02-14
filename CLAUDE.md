# Jarvis — Personal AI Assistant

## Project Overview

A Python personal AI assistant built on **Letta** (self-hosted) using **Anthropic Claude** as the LLM. Connects to Slack, WhatsApp Web, and Google Chat. Supports shell execution, browser automation, cron scheduling, Gmail, Google Calendar, Notion, and proactive monitoring.

## Tech Stack

- **Language**: Python 3.11+
- **Package manager**: uv (no pip, no venv)
- **Agent backbone**: Letta (self-hosted via Docker)
- **LLM**: Configurable — OpenAI, Anthropic, or Google Gemini (via Letta). Currently `openai/gpt-5.2`.
- **Database**: PostgreSQL + pgvector (managed by Letta)
- **Testing**: pytest, pytest-asyncio
- **Linting**: ruff
- **Type checking**: mypy (strict)
- **Logging**: structlog
- **Config**: Pydantic Settings + YAML

## Conventions

- **TDD**: Tests written before/alongside code, never after. Every phase has mock + real validation gates.
- **uv everywhere**: `uv run pytest`, `uv run python -m jarvis`, `uv add <pkg>`.
- **Self-contained tools**: Letta tools are plain Python functions with all imports inside function body. Credentials via `os.environ`.
- **Channel ABC**: All messaging platforms implement the same abstract interface.
- **Single agent**: One Letta agent with unified memory across all channels.
- **Internal HTTP bridge**: Letta sandbox tools communicate with app via `http://localhost:9100`.
- **Structured logging**: structlog from day one. No print statements.
- **YAML config**: Human-readable `config/jarvis.yaml` for all settings.
- **Commit style**: Conventional — lowercase, imperative mood, concise. **No Co-Authored-By lines.**
- **Git workflow**: Each phase gets its own branch off main (`phase-N-description`). Commit + push when phase passes. User merges to main manually and signals to proceed to next phase.

## Project Structure

```
jarvis/
├── CLAUDE.md              ← you are here
├── pyproject.toml         # uv-managed
├── Makefile               # test, lint, run shortcuts
├── config/jarvis.yaml     # main config
├── docs/
│   ├── desiderata.md      # immutable principles
│   ├── process.md         # phase lifecycle
│   └── phases/            # per-phase plan + retro
├── src/jarvis/            # main source
├── tests/                 # unit, integration, e2e
└── scripts/               # setup and utility scripts
```

## Key References

- `docs/desiderata.md` — Immutable project principles (read before making architectural decisions)
- `docs/process.md` — Phase lifecycle: PLAN → TEST → IMPLEMENT → RETRO
- `docs/phases/` — Per-phase plans and retrospectives

## Current State

- **Current phase**: 12 (Agent Evaluation Framework) — COMPLETE
- **Next phase**: None planned
- **What exists**: Full message loop + tools + Slack + WhatsApp + scheduler + proactive messaging + Gmail + Google Calendar + Notion + Google Slides + Google Docs + Google Sheets + Todoist + Browser automation + Memory & Learning + Monitoring + Docker + Voice STT/TTS + Security Hardening + Agent Evals. HTTP bridge has 42 endpoints with optional bearer token auth. 44 tools registered with Letta agent. Three active channels: CLI, Slack, WhatsApp — all with voice I/O support. 308 unit + 16 integration = 324 tests — all passing (integration skipped without Letta server).
- **Evals**: Offline-first evaluation framework. 20 golden scenarios covering all tool categories. Mock Letta client for CI-safe offline eval. Online mode via `--agent-id` against live Letta. LLM-as-judge scoring (gpt-4o-mini). CLI: `python -m jarvis.evals [--no-judge] [--tags ...] [--format text|json] [--agent-id ID]`. Live results (n=10): **86% mean tool-routing accuracy** (SD=5%, range 80-95%). 14/20 scenarios stable at 100%. Known limitations: single prompt per tool, single-turn only, subset matching, 20/44 tools covered. `TOOL_INVOCATION_COUNT` now wired in router.
- **Security**: Bearer token auth on HTTP bridge, shell command safety filter, WhatsApp sender allowlist, file path sandboxing (home dir jail), browser SSRF prevention, Docker hardened (no exposed DB port, request size limits), graceful SIGTERM shutdown.
- **Voice**: OpenAI Whisper STT + TTS (tts-1). VoiceService class wraps OpenAI API. Router-level integration: transcribes inbound audio, synthesizes outbound. tts_mode: "auto" (voice reply only for voice input), "always", "never". WhatsApp voice notes via Baileys `downloadMediaMessage`/`sendMessage({audio, ptt})`. Slack audio file download/upload. CLI full voice I/O via `sounddevice` (mic recording + audio playback).
- **Monitoring**: Prometheus metrics (HTTP requests, tool invocations, messages, errors), configurable structlog renderer (console/JSON), aiohttp observability middleware, enhanced `/health` endpoint with Letta connectivity check, `/metrics` endpoint.
- **Docker**: Multi-stage Dockerfile (python:3.11-slim + Playwright Chromium), `docker-compose.yml` with 4 services (letta_db, letta_server, jarvis, whatsapp_bridge), health checks on all services, `jarvis-docker.yaml` with service discovery hostnames.

## Known Gotchas

- **Letta pagination**: `client.agents.list()` returns `SyncArrayPage`, not a list. Use `.items` to get results. Mocks return plain lists, so use `hasattr(page, "items")` guard.
- **Docker `restart` vs `recreate`**: `docker compose restart` does NOT re-read `env_file`. Use `docker compose up -d --force-recreate` when `.env` changes.
- **Google/Gemini provider**: Letta does not auto-detect Google. Must register manually via `POST /v1/providers/` with `provider_type: "google_ai"`. OpenAI and Anthropic are auto-synced.
- **pgvector extension**: Letta crashes on startup without `CREATE EXTENSION IF NOT EXISTS vector;`. The `init.sql` mounted into the PostgreSQL entrypoint handles this.
- **Hatchling build backend**: Must have `[build-system]` with hatchling and `[tool.hatch.build.targets.wheel] packages = ["src/jarvis"]` for `import jarvis` to work.
- **Letta tool type hints**: Schema generation rejects union types (`str | None`, `Optional[str]`). Use only primitive types (`str`, `int`, `bool`, `float`) with simple defaults (e.g., `workdir: str = ""`).
- **AsyncIOScheduler needs event loop**: APScheduler's `AsyncIOScheduler` requires a running event loop at `start()`. Use `BackgroundScheduler` instead, with `_invoke()` wrapper that dispatches async callbacks via `run_coroutine_threadsafe()`.
- **Trigger dual-path notification**: Agent responses to `[scheduler|system]` messages go nowhere (no channel context). The trigger must send notifications directly via router AND inform the agent for memory.
- **Persona block updates on running agent**: Changing `persona.py` only affects new agents. Existing agents need `PATCH /v1/blocks/<id>` via Letta API.
- **Message prefix format**: `[channel|user_id|display_name]` — three fields, pipe-separated. The raw user ID is needed for `send_message_to_user` and `create_reminder` routing.
- **Commit style**: No Co-Authored-By lines.
- **GCP OAuth consent screen**: Must be set to "External" (not "Internal") for personal Google accounts. Add your email as a test user. "Testing" mode is fine for personal projects.
- **Letta tool pagination on agents.tools.list()**: Default page size is small. With 18+ tools, use `limit=100` to get all attached tools.
- **Google token file**: `google_token.json` at project root (gitignored). Override with `GOOGLE_TOKEN_PATH` env var. Generated by `scripts/setup_google_oauth.py`.
- **Google API calls are synchronous**: `googleapiclient` is sync. HTTP server wraps in `asyncio.to_thread()` to avoid blocking.
- **Baileys auth on logout**: After WhatsApp logout, stale auth in Docker volume causes 401 loop. Bridge clears auth directory *contents* (not the dir itself — EBUSY on volume mount) and shows new QR.
- **`source .env` doesn't export**: Use `set -a && source .env && set +a` before `uv run python -m jarvis` so env vars reach child processes.
- **WhatsApp webhook URL in Docker**: Bridge uses `http://host.docker.internal:9100/whatsapp/inbound`. Works on macOS/Windows Docker Desktop. Linux may need `--add-host` or host network mode.
- **Agent leaks internal IDs**: Without PRIVACY persona section, agent may expose Slack channel IDs or WhatsApp JIDs to users on other channels. Persona block now includes instructions to never expose internal identifiers.
- **Playwright lazy singleton in tests**: Browser handlers use module-level `_browser`, `_context`, `_pw`. Tests must reset all three to `None` before each test case to avoid state leaks. Mock chain: `sync_playwright()` → `.start()` → pw instance.
- **Notion `_extract_title` requires `"type": "title"` key**: The Notion API response includes `"type": "title"` in each property dict. Mock data in tests must include this key or title extraction returns `"(untitled)"`.
- **Slides listing needs Drive API**: The `presentations` scope alone can't list files. Need `drive.readonly` scope + `drive.files().list(q="mimeType='application/vnd.google-apps.presentation'")`.
- **Integration conftest skips all tests**: `tests/integration/conftest.py` has `pytest_collection_modifyitems` that marks ALL collected items (including unit tests) as skip when Letta is unreachable. Fixed to only skip `tests/integration/` items, but keep in mind when adding conftest hooks.
- **With 30+ tools**: Use `limit=100` on `agents.tools.list()` to get all attached tools (Letta default page size is small).
- **aiohttp middleware must re-raise `web.HTTPException`**: The observability middleware catches `Exception` for 500 handling, but `web.HTTPNotFound` etc. are exceptions too. Must `except web.HTTPException: raise` before the generic `except Exception`.
- **aiohttp `content_type` with charset**: `web.Response(content_type="text/plain; charset=utf-8")` raises — charset must not be in the content_type arg. Use `headers={"Content-Type": ...}` instead.
- **`get_or_create_agent` returns tuple**: `(agent, tool_count)` — only `app.py` calls this, but any test that calls it must unpack.
- **Prometheus counter testing**: Use delta-based assertions (read before, act, read after). Global registry is shared across tests.
- **Docker Jarvis config**: Set `JARVIS_CONFIG=/app/config/jarvis-docker.yaml` env var in compose. Uses service names for discovery (letta_server, whatsapp_bridge).
- **Google API enablement**: OAuth scopes alone are not enough — each Google API (Docs, Sheets, Slides, etc.) must be separately **enabled** in the GCP console at `console.developers.google.com/apis/api/{api}.googleapis.com/overview`. First call will 403 if API is disabled.
- **Google OAuth re-auth on new scopes**: Adding new scopes to `auth.py` + `setup_google_oauth.py` requires deleting `google_token.json` and re-running `uv run python scripts/setup_google_oauth.py`. Existing tokens won't have the new scopes.
- **Google Docs `endOfSegmentLocation`**: Empty `{}` dict inserts at end of body. Get doc first to find end index via `body.content[-1].endIndex - 1`.
- **Sheets `values_json` workaround**: Letta tool type hints reject complex types. Pass `values_json: str` and `json.loads()` in the handler. Same pattern for any structured data.
- **Todoist `due` field**: Can be `null` or a dict with `string`, `date`, `datetime` keys. Handle both cases when displaying.
- **Letta passages API (formerly archival_memory)**: Use `client.agents.passages.create(agent_id, text=..., tags=[...])` for insert, `client.agents.passages.search(agent_id, query=..., top_k=N)` for search. Search returns `PassageSearchResponse` with `.results` list of `Result` objects having `.content` (not `.text`), `.timestamp` (not `.created_at`), `.tags`.
- **Letta `agents.blocks.list()` returns `SyncArrayPage`**: Same pagination pattern as `agents.list()`. Use `.items` guard: `page.items if hasattr(page, "items") else page`.
- **Prometheus counter test isolation**: Global Prometheus registry is shared. Learning cycle tests need explicit counter increments before running, otherwise `collect_usage_stats()` returns empty data and the cycle skips.
- **OpenAI Whisper needs file extension**: `transcriptions.create()` infers format from filename. Must write temp file with correct extension (`.ogg`, `.mp3`, etc.) not just `.tmp`.
- **WhatsApp voice notes are OGG/Opus**: Baileys `audioMessage` uses `audio/ogg; codecs=opus`. Whisper supports this natively.
- **Slack audio clips are `audio/mp4`**: Native Slack audio clips have MIME `audio/mp4`, filetype `m4a`, name `audio_message.m4a`. Re-uploaded clips come as `video/mp4`. Detection checks both `audio/*` and `video/mp4` with `audio_message` filename.
- **Slack `file_share` subtype**: Audio clips arrive as message events with `subtype: file_share`. Bolt's `@app.message()` ignores subtypes by default — must use `@app.event("message")` with an allowlist in `_should_skip`.
- **Slack file download redirect strips auth**: `url_private_download` redirects to a CDN. `aiohttp` strips `Authorization` header on cross-origin redirects, returning an HTML page instead of audio. Fix: `allow_redirects=False` + manually follow redirect (CDN URL is pre-signed, no auth needed).
- **Slack bot scopes for voice**: Needs `files:read` (download audio) + `files:write` (upload audio reply). Must reinstall app after adding scopes. Audio upload failure is caught and falls back to text-only.
- **Whisper file tuple**: Pass `file=(filename, bytes)` tuple to `transcriptions.create()` instead of temp files — avoids temp file issues in containers.
- **`express.json()` default limit is 100kb**: Base64 audio can be several MB. Bridge uses `{ limit: '10mb' }`.
- **TTS output must be OGG/Opus for WhatsApp**: OpenAI TTS with `response_format="opus"` produces OGG/Opus. MP3 with `ptt: true` is silently dropped by WhatsApp — audio appears sent but never delivered. Always use Opus for voice notes.
- **sounddevice needs PortAudio**: On macOS `brew install portaudio`, on Linux `apt-get install libportaudio2`. In Docker (no mic/speaker), `_ensure_audio_libs()` returns `False` and CLI voice gracefully disables itself.
- **CLI voice lazy imports**: `sounddevice` and `soundfile` are lazy-imported in `cli.py` via `_ensure_audio_libs()`. If PortAudio is missing (Docker), voice mode auto-disables instead of crashing.
- **Router STT/TTS outside Letta lock**: Voice transcription and synthesis happen outside `self._lock` to avoid blocking other messages during audio processing.
- **OpenAI API key reuse**: Voice service uses `OPENAI_API_KEY` — same env var as Letta embeddings. No separate key needed.
