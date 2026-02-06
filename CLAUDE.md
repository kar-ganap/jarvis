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

- **Current phase**: 5 (Gmail + Google Calendar) — COMPLETE
- **Next phase**: 6 (WhatsApp Channel)
- **What exists**: Full message loop + tools + Slack + scheduler + proactive messaging + Gmail + Google Calendar. HTTP bridge now has 13 endpoints (health, outbound, 4 scheduler, 4 Gmail, 4 GCal). Google OAuth2 desktop flow with auto-refresh. Tools: `gmail_search`, `gmail_read`, `gmail_send`, `gmail_draft`, `gcal_list_events`, `gcal_create_event`, `gcal_update_event`, `gcal_delete_event`. 104 unit + 12 integration = 116 tests — all passing. Live Slack verified: "what's on my calendar today?" → real events, "what's the latest email" → real email content.
- **What's next**: WhatsApp channel via Node.js Baileys bridge, cross-channel memory verification

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
