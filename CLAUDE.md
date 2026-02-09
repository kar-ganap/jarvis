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

- **Current phase**: 8 (Docker + Monitoring) — COMPLETE
- **Next phase**: 9 (Google Docs/Sheets + Todoist + Memory & Learning)
- **What exists**: Full message loop + tools + Slack + WhatsApp + scheduler + proactive messaging + Gmail + Google Calendar + Notion + Google Slides + Browser automation + Monitoring + Docker. HTTP bridge has 28 endpoints (enhanced health, metrics, outbound, whatsapp/inbound, 4 scheduler, 4 Gmail, 4 GCal, 4 Slides, 5 Notion, 3 Browser). 30 tools registered with Letta agent. Three active channels: CLI, Slack, WhatsApp. 187 unit + 16 integration = 203 tests — all passing (integration skipped without Letta server).
- **Monitoring**: Prometheus metrics (HTTP requests, tool invocations, messages, errors), configurable structlog renderer (console/JSON), aiohttp observability middleware, enhanced `/health` endpoint with Letta connectivity check, `/metrics` endpoint.
- **Docker**: Multi-stage Dockerfile (python:3.11-slim + Playwright Chromium), `docker-compose.yml` with 4 services (letta_db, letta_server, jarvis, whatsapp_bridge), health checks on all services, `jarvis-docker.yaml` with service discovery hostnames.
- **Google Slides**: Live-validated. All 4 endpoints working (list, create, read, add_slide with text insertion). Fixed `gslides_add_slide` to use `placeholderIdMappings` + `insertText` for title/body.

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
