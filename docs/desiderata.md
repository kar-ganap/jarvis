# Desiderata — Immutable Project Principles

These principles are established at project inception and do not change. All architectural decisions, code reviews, and phase plans must be consistent with them.

---

## 1. Python + uv

- Python 3.11+ is the sole language for the assistant (Node.js Baileys bridge is the one exception).
- **uv** is the package manager. No pip, no venv, no poetry, no conda.
- All commands run through uv: `uv run pytest`, `uv run python -m jarvis`, `uv add <pkg>`.

## 2. Test-Driven Development

- Tests are written **before or alongside** code, never after.
- Every phase has a **validation gate** with two tiers:
  - **Mock tests** (`tests/unit/`): No external dependencies. Mocked Letta client, mocked APIs.
  - **Real tests** (`tests/integration/`): Against running Letta server and real services where applicable.
- A phase is **not complete** until both tiers pass.
- TDD flow: write failing test (red) → implement (green) → refactor → commit.

## 3. Don't Rebuild What Letta Provides

Letta gives us:
- Agent loop (message processing, tool calling, reasoning)
- 3-tier memory (blocks, message history, archival/pgvector)
- Tool framework (register Python functions → JSON schemas → sandbox execution)
- Persistence (PostgreSQL checkpointing every agent step)
- Context management (automatic compaction)

We build **on top of** Letta, not around it. If Letta has a mechanism for something, use it.

## 4. Security

- No credentials in code. All secrets via environment variables or `.env` (gitignored).
- Shell execution: environment variable filtering, workspace-scoped paths.
- File operations: scoped to allowed directories.
- Tool sandbox: Letta's sandbox is the execution boundary. Tools cannot access app memory directly.

## 5. Clean Abstractions

- **Channel ABC**: All messaging platforms implement the same abstract interface (`start`, `stop`, `send`, `health_check`).
- **Tool registry pattern**: Tools are self-contained Python functions with all imports inside function body. Discovered and registered programmatically.
- **Message normalization**: All inbound messages become `ChannelMessage`. All outbound become `OutboundMessage`.

## 6. Configuration

- Human-readable YAML config (`config/jarvis.yaml`) for all settings.
- Pydantic Settings model validates and types the config.
- Environment variables override YAML values where appropriate.

## 7. Structured Logging

- **structlog** from day one. No `print()` statements.
- Log levels used consistently: DEBUG for internals, INFO for lifecycle events, WARNING for degraded states, ERROR for failures.

## 8. Git Workflow

- Each phase gets its own branch off `main` (e.g., `phase-0-infrastructure`).
- Commit and push when the phase validation gate passes.
- User merges to `main` manually and signals to proceed to the next phase.
- No force pushes. No commits to `main` directly.

## 9. Documentation as Code

- `CLAUDE.md` is the living project state — updated at the end of every phase.
- `docs/phases/phase-N-plan.md` written before implementation starts.
- `docs/phases/phase-N-retro.md` written after phase completes.
- Process and principles docs live in the repo, not in external tools.
