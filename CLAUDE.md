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

- **Current phase**: 2 (First Tools — Shell + Web Search + File Ops) — COMPLETE
- **Next phase**: 3 (Slack Channel)
- **What exists**: Full message loop + 3 tool categories. Tool registry (`collect_tools`, `register_tools`, `sync_agent_tools`), `execute_shell_command`, `web_search` (Tavily), `read_file`/`write_file`/`list_directory`. Agent autonomously uses tools when asked. 50 unit + 7 integration tests — all passing.
- **What's next**: Slack channel (Socket Mode), channel registry for enabled channels from config

## Known Gotchas

- **Letta pagination**: `client.agents.list()` returns `SyncArrayPage`, not a list. Use `.items` to get results. Mocks return plain lists, so use `hasattr(page, "items")` guard.
- **Docker `restart` vs `recreate`**: `docker compose restart` does NOT re-read `env_file`. Use `docker compose up -d --force-recreate` when `.env` changes.
- **Google/Gemini provider**: Letta does not auto-detect Google. Must register manually via `POST /v1/providers/` with `provider_type: "google_ai"`. OpenAI and Anthropic are auto-synced.
- **pgvector extension**: Letta crashes on startup without `CREATE EXTENSION IF NOT EXISTS vector;`. The `init.sql` mounted into the PostgreSQL entrypoint handles this.
- **Hatchling build backend**: Must have `[build-system]` with hatchling and `[tool.hatch.build.targets.wheel] packages = ["src/jarvis"]` for `import jarvis` to work.
- **Letta tool type hints**: Schema generation rejects union types (`str | None`, `Optional[str]`). Use only primitive types (`str`, `int`, `bool`, `float`) with simple defaults (e.g., `workdir: str = ""`).
- **Commit style**: No Co-Authored-By lines.
