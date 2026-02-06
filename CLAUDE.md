# Jarvis — Personal AI Assistant

## Project Overview

A Python personal AI assistant built on **Letta** (self-hosted) using **Anthropic Claude** as the LLM. Connects to Slack, WhatsApp Web, and Google Chat. Supports shell execution, browser automation, cron scheduling, Gmail, Google Calendar, Notion, and proactive monitoring.

## Tech Stack

- **Language**: Python 3.11+
- **Package manager**: uv (no pip, no venv)
- **Agent backbone**: Letta (self-hosted via Docker)
- **LLM**: Anthropic Claude (via Letta)
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

- **Current phase**: 0.0 (Meta) — COMPLETE
- **Next phase**: 0 (Infrastructure)
- **What exists**: Project skeleton, process docs, no code yet
- **What's next**: docker-compose.yml, settings.py, agent factory, Makefile, first tests

## Known Gotchas

_(Updated after each phase retro)_
