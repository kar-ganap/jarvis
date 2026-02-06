# Phase 0 Plan: Infrastructure

## Goal

Stand up the foundational infrastructure: Letta server running in Docker, Python project wired with dependencies, configuration loading, agent creation, and utility scripts. No channels, no tools, no routing — just the base layer everything else builds on.

---

## File-by-File Breakdown

### 1. `docker-compose.yml`

Letta server + PostgreSQL/pgvector. Stripped-down version of the official compose — no nginx, no telemetry.

```yaml
services:
  letta_db:
    image: ankane/pgvector:v0.5.1
    environment:
      POSTGRES_USER: letta
      POSTGRES_PASSWORD: letta
      POSTGRES_DB: letta
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U letta"]
      interval: 5s
      timeout: 5s
      retries: 5

  letta_server:
    image: letta/letta:latest
    depends_on:
      letta_db:
        condition: service_healthy
    ports:
      - "8283:8283"
    env_file:
      - .env
    environment:
      - LETTA_PG_URI=postgresql://letta:letta@letta_db:5432/letta

volumes:
  pgdata:
```

Key decisions:
- Named volume `pgdata` (not bind mount) — cleaner, Docker manages it
- Only expose port 8283 (the current standard API port)
- `.env` file supplies `ANTHROPIC_API_KEY` (and optionally `OPENAI_API_KEY` for embeddings)
- No nginx proxy — unnecessary for local dev

### 2. `pyproject.toml` (update)

Add Phase 0 dependencies:

```
# Core
letta-client
pydantic-settings
pyyaml
structlog

# Dev
pytest
pytest-asyncio
pytest-timeout
ruff
mypy
```

### 3. `config/jarvis.yaml`

Default configuration file. Minimal for Phase 0 — just agent and Letta settings.

```yaml
letta:
  base_url: "http://localhost:8283"

agent:
  name: "jarvis"
  model: "anthropic/claude-sonnet-4-20250514"
  embedding: "openai/text-embedding-3-small"
  context_window_limit: 30000

user:
  name: "Kartik"
  preferred_channel: "cli"
```

Key decisions:
- Claude Sonnet 4 as default model (good balance of capability and cost for dev)
- OpenAI text-embedding-3-small for embeddings (Anthropic doesn't provide embeddings; letta-free is an option but OpenAI is more reliable)
- context_window_limit=30000 to avoid runaway token costs during dev

### 4. `src/jarvis/__init__.py`

Empty init. Package marker.

### 5. `src/jarvis/settings.py`

Pydantic Settings model that loads from YAML + env vars.

```python
class LettaSettings(BaseModel):
    base_url: str = "http://localhost:8283"

class AgentSettings(BaseModel):
    name: str = "jarvis"
    model: str = "anthropic/claude-sonnet-4-20250514"
    embedding: str = "openai/text-embedding-3-small"
    context_window_limit: int = 30000

class UserSettings(BaseModel):
    name: str = "User"
    preferred_channel: str = "cli"

class JarvisSettings(BaseModel):
    letta: LettaSettings
    agent: AgentSettings
    user: UserSettings

def load_settings(config_path: Path | None = None) -> JarvisSettings:
    """Load settings from YAML file, with env var overrides."""
    # 1. Find config file (explicit path > JARVIS_CONFIG env > default)
    # 2. Parse YAML
    # 3. Construct JarvisSettings
    # 4. Override with env vars where applicable
```

Key decisions:
- Plain Pydantic BaseModel (not pydantic-settings BaseSettings) — we control YAML loading ourselves
- `load_settings()` is a function, not a class method — easier to test with different configs
- Env var `JARVIS_CONFIG` can override config file path
- Individual env vars like `LETTA_BASE_URL` can override nested YAML values

### 6. `src/jarvis/agent/`

#### `agent/__init__.py` — empty

#### `agent/persona.py`

Persona and human memory block text generators.

```python
def build_persona_block(agent_name: str = "Jarvis") -> str:
    """Return the persona block text for the agent."""
    # Returns a multi-line string defining the agent's identity,
    # capabilities, and behavioral guidelines.

def build_human_block(user_name: str = "User") -> str:
    """Return the human block text for the agent."""
    # Returns a multi-line string with user info placeholder.
```

These are pure functions returning strings — no Letta dependency, easily testable.

#### `agent/factory.py`

Agent creation / retrieval.

```python
from letta_client import Letta

def get_or_create_agent(client: Letta, settings: JarvisSettings) -> Agent:
    """Get existing agent by name or create a new one."""
    # 1. List agents filtered by name
    # 2. If found, return existing agent
    # 3. If not found, create new agent with:
    #    - model from settings
    #    - embedding from settings
    #    - persona block from persona.py
    #    - human block from persona.py
    #    - include_base_tools=True (memory editing tools)
    #    - context_window_limit from settings
    # 4. Return created agent
```

Key decisions:
- Idempotent: calling twice with same name returns the same agent
- `client` is injected (not created inside) — testable with mock
- Returns the Letta Agent object directly

### 7. `scripts/seed_agent.py`

Interactive script to create the agent and verify it works.

```python
"""Create the Jarvis agent and send a test message."""
# 1. Load settings
# 2. Create Letta client
# 3. Call get_or_create_agent()
# 4. Send a test message: "Hello, introduce yourself briefly."
# 5. Print the assistant's response
# 6. Print agent ID and block info
```

### 8. `scripts/healthcheck.py`

Check if Letta server is reachable.

```python
"""Check Letta server health."""
# 1. Load settings (just need base_url)
# 2. Create Letta client
# 3. Try listing agents (limit=1) as a health probe
# 4. Print success/failure with server URL
# 5. Exit code 0 on success, 1 on failure
```

### 9. `Makefile`

```makefile
.PHONY: test test-all test-int lint typecheck docker-up docker-down run seed health

test:
	uv run pytest tests/unit/ -v

test-all:
	uv run pytest tests/ -v

test-int:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run mypy src/jarvis/

docker-up:
	docker compose up -d

docker-down:
	docker compose down

run:
	uv run python -m jarvis

seed:
	uv run python scripts/seed_agent.py

health:
	uv run python scripts/healthcheck.py
```

### 10. `.env.example` (update)

Add the embedding key note:

```bash
# Letta server
LETTA_BASE_URL=http://localhost:8283

# Anthropic (required — used by Letta for Claude)
ANTHROPIC_API_KEY=

# OpenAI (required for embeddings — Anthropic doesn't provide embeddings)
OPENAI_API_KEY=

# Slack (Phase 3)
# SLACK_BOT_TOKEN=
# SLACK_APP_TOKEN=
```

### 11. `src/jarvis/utils/__init__.py` and `src/jarvis/utils/logging.py`

Structlog configuration. Minimal for Phase 0.

```python
import structlog

def setup_logging(debug: bool = False) -> None:
    """Configure structlog for the application."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),  # pretty for dev
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

---

## Test Plan

### Unit Tests (Mock) — `tests/unit/`

#### `tests/unit/test_settings.py`

1. **test_load_settings_from_yaml** — Load a valid YAML config, verify all fields populated correctly
2. **test_load_settings_defaults** — Load minimal YAML (empty sections), verify defaults apply
3. **test_load_settings_missing_file** — Non-existent config path raises FileNotFoundError
4. **test_load_settings_env_override** — Set `JARVIS_CONFIG` env var, verify it's used as config path

#### `tests/unit/test_persona.py`

1. **test_build_persona_block_default** — Default persona contains agent name "Jarvis"
2. **test_build_persona_block_custom_name** — Custom name appears in persona text
3. **test_build_human_block_default** — Default human block contains "User"
4. **test_build_human_block_custom_name** — Custom name appears in human block text
5. **test_persona_block_not_empty** — Persona text is non-empty and substantial (>100 chars)
6. **test_human_block_not_empty** — Human text is non-empty

#### `tests/unit/test_factory.py`

1. **test_get_or_create_agent_creates_new** — Mock client returns empty list for agents.list() → calls agents.create() with correct params
2. **test_get_or_create_agent_returns_existing** — Mock client returns existing agent → does NOT call agents.create()
3. **test_get_or_create_agent_passes_settings** — Verify model, embedding, context_window_limit from settings are passed to create()

#### `tests/conftest.py`

Shared fixtures:
- `mock_letta_client` — MagicMock of Letta client with nested `.agents.list()`, `.agents.create()`, `.agents.messages.create()`
- `test_settings` — JarvisSettings loaded from a test YAML fixture
- `tmp_config` — Temporary YAML config file for settings tests

### Integration Tests (Real Letta) — `tests/integration/`

#### `tests/integration/conftest.py`

- `letta_client` fixture — Creates real Letta client from settings, skips if server unreachable
- `skip_if_no_letta` marker — Auto-skip when docker compose not running

#### `tests/integration/test_healthcheck.py`

1. **test_letta_server_reachable** — List agents succeeds (proves server is up)

#### `tests/integration/test_agent_creation.py`

1. **test_create_agent** — Create agent with test name, verify it has persona + human blocks
2. **test_agent_responds** — Send "Hello" to agent, get back an assistant_message with non-empty content
3. **test_agent_idempotent** — Create same agent twice, verify same agent ID returned
4. Teardown: delete test agent after each test

---

## Acceptance Criteria (Validation Gate)

Phase 0 is **complete** when:

1. `docker compose up -d` starts Letta server + PostgreSQL successfully
2. `uv run pytest tests/unit/ -v` — all unit tests pass
3. `uv run pytest tests/integration/ -v` — all integration tests pass (with docker compose up)
4. `uv run ruff check src/ tests/` — no lint errors
5. `uv run python scripts/healthcheck.py` — prints success
6. `uv run python scripts/seed_agent.py` — creates agent and prints Claude's response

---

## Dependencies / Blockers

- **Docker** must be installed and running (for docker compose)
- **ANTHROPIC_API_KEY** must be set in `.env` (for Claude via Letta)
- **OPENAI_API_KEY** must be set in `.env` (for embeddings) — OR we use `letta-free` embedding
- No blockers from other phases

---

## Open Questions

1. **Embedding provider**: OpenAI text-embedding-3-small (costs money, reliable) vs letta-free (free, hosted by Letta team). Will try letta-free first for dev; switch to OpenAI if quality issues arise.
