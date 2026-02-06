# Phase 0 Retro: Infrastructure

## What Worked
- TDD flow worked well — 13 unit tests written first (all red), then implementation made them green in one pass
- `uv init` + `uv add` was seamless — project bootstrapped in seconds
- Letta SDK API is clean: `client.agents.create()`, `client.agents.messages.create()` — intuitive
- Integration tests auto-skip via `pytest_collection_modifyitems` when Letta isn't running — no manual markers needed
- LLM provider swapping is pure config — changed from Anthropic to OpenAI by editing one YAML line, zero code changes
- Seed script produced a working agent on first try once the model was right

## Surprises
- **Letta SDK pagination**: `client.agents.list()` returns `SyncArrayPage`, not a plain list. Must use `.items` to get the actual list. Mocks return plain lists, so the factory needed `hasattr(page, "items")` to handle both.
- **Anthropic credit issue**: The Anthropic API key had insufficient credits, which blocked `test_agent_responds`. Switched to OpenAI `gpt-5.2` which worked immediately. Discovered this is a billing issue, not a code issue.
- **Google/Gemini provider registration**: Letta 0.16.4 does NOT auto-detect Google as a provider from `GOOGLE_API_KEY` env var. Only `openai`, `anthropic`, and `letta` are auto-synced. Google must be registered manually via `POST /v1/providers/` REST API.
- **Docker `restart` vs `recreate`**: `docker compose restart` does NOT re-read `env_file`. Must use `docker compose up -d --force-recreate` when `.env` changes. This wasted two debug cycles.
- **pgvector extension**: The Letta server crashes on startup if the `vector` extension isn't created in PostgreSQL. The official compose.yaml uses an `init.sql` mounted into the entrypoint — we missed this initially.
- **`hatchling` build backend**: `uv init` doesn't set up a build backend. Had to add `[build-system]` with hatchling and `[tool.hatch.build.targets.wheel]` to make `src/jarvis/` importable.

## Deviations from Plan
- **Model changed**: Plan specified `anthropic/claude-sonnet-4-20250514`. Switched to `openai/gpt-5.2` due to Anthropic billing. Config-only change, no code impact.
- **Google provider**: Not in the original Phase 0 plan. Added because user wanted multi-provider support confirmed early. Required manual REST API call to register.
- **`init.sql`**: Not in the plan. Discovered during Docker setup that pgvector extension must be explicitly created.

## Assumptions Made Explicit
- Letta's `agents.list()` returns paginated objects, not plain lists — all code consuming this API must handle pagination
- Docker `env_file` is read at container creation time only, not on restart
- Google/Gemini provider must be manually registered with Letta — it's not auto-detected
- The Anthropic API key needs active billing credits to make LLM calls through Letta
- OpenAI embeddings (`text-embedding-3-small`) work regardless of which LLM provider is used for chat

## Scope Changes for Next Phase
- **Added**: `seed_agent.py` should auto-register Google provider if `GOOGLE_API_KEY` is set
- **No removals**

## Key Decisions and Rationale
- **OpenAI as default model**: `openai/gpt-5.2` chosen for reliability and working billing. Can switch to Anthropic or Gemini via config when credits are available.
- **`hasattr` guard in factory**: Rather than forcing mocks to replicate pagination, we check `hasattr(page, "items")`. Pragmatic over pure — keeps unit tests simple.
- **Named Docker volume**: `pgdata` as a named volume (not bind mount) — Docker manages it, cleaner than `.persist/` directories.

## Metrics
- Tests: 13 unit, 4 integration (all passing)
- Files created: 22 (including tests, configs, scripts, docs)
- Lines of code: ~350 (src) + ~200 (tests)
- Dependencies: 6 core + 5 dev
