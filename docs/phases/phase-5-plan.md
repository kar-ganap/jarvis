# Phase 5: Gmail + Google Calendar — Implementation Plan

## Design Decision: HTTP Bridge Pattern

Letta tools run in a sandbox that only has `requests`. They can't use `google-api-python-client` directly. So:
- **Letta tools** (`tools/gmail.py`, `tools/gcal.py`) → POST to `http://host.docker.internal:9100/google/*`
- **HTTP server** (`http_server.py`) → routes to handler functions
- **Handler functions** (`google/handlers.py`) → use `google-api-python-client` with credentials from `google/auth.py`

This follows the same pattern used for scheduler tools in Phase 4.

## Files to Create (7 new)

### 1. `scripts/setup_google_oauth.py` — One-time OAuth setup
- `InstalledAppFlow.from_client_secrets_file("gcp_oauth_client_id.json", SCOPES)`
- `flow.run_local_server(port=0)` → interactive browser auth
- Saves token to `google_token.json` (gitignored)
- Scopes: `gmail.modify`, `calendar.events`

### 2. `src/jarvis/google/__init__.py` — Empty

### 3. `src/jarvis/google/auth.py` — Token management
- `get_credentials() -> Credentials` — loads `google_token.json`, auto-refreshes if expired
- Reads token path from `GOOGLE_TOKEN_PATH` env var (default: `google_token.json` at project root)
- Returns `google.oauth2.credentials.Credentials`

### 4. `src/jarvis/google/handlers.py` — 8 HTTP endpoint handlers
Gmail (4):
- `handle_gmail_search(request)` — query string search, returns list of {id, subject, from, date, snippet}
- `handle_gmail_read(request)` — read single email by ID, returns {subject, from, to, date, body}
- `handle_gmail_send(request)` — compose + send email, returns {id, thread_id}
- `handle_gmail_draft(request)` — create draft, returns {id, message_id}

Calendar (4):
- `handle_gcal_list(request)` — list events in time range, returns [{id, summary, start, end, location}]
- `handle_gcal_create(request)` — create event, returns {id, html_link}
- `handle_gcal_update(request)` — update event by ID, returns {id, html_link}
- `handle_gcal_delete(request)` — delete event by ID, returns {status: "deleted"}

All handlers: use `get_credentials()` → build service → call API → return JSON.

### 5. `src/jarvis/tools/gmail.py` — 4 Letta tool functions
- `gmail_search(query: str, max_results: int = 5) -> str`
- `gmail_read(message_id: str) -> str`
- `gmail_send(to: str, subject: str, body: str) -> str`
- `gmail_draft(to: str, subject: str, body: str) -> str`
- All: `requests.post(f"http://{host}:{port}/google/gmail/...")` → format response as readable text
- `TOOLS = [gmail_search, gmail_read, gmail_send, gmail_draft]`

### 6. `src/jarvis/tools/gcal.py` — 4 Letta tool functions
- `gcal_list_events(days_ahead: int = 1) -> str`
- `gcal_create_event(summary: str, start_time: str, end_time: str, description: str = "", location: str = "") -> str`
- `gcal_update_event(event_id: str, summary: str = "", start_time: str = "", end_time: str = "", description: str = "", location: str = "") -> str`
- `gcal_delete_event(event_id: str) -> str`
- All: `requests.post/get(f"http://{host}:{port}/google/gcal/...")` → format response as readable text
- `TOOLS = [gcal_list_events, gcal_create_event, gcal_update_event, gcal_delete_event]`

### 7. `docs/phases/phase-5-plan.md` — Copy of this plan for project docs

## Files to Modify (7 existing)

### 8. `src/jarvis/http_server.py` — Add 8 Google routes
```
POST /google/gmail/search
POST /google/gmail/read
POST /google/gmail/send
POST /google/gmail/draft
POST /google/gcal/list
POST /google/gcal/create
POST /google/gcal/update
POST /google/gcal/delete
```
Import handlers from `google/handlers.py`, wire into `_build_app()`.

### 9. `src/jarvis/settings.py` — Add `GoogleSettings`
```python
class GoogleSettings(BaseModel):
    client_secrets_path: str = "gcp_oauth_client_id.json"
    token_path: str = "google_token.json"
```
Add to `JarvisSettings` and `load_settings()`.

### 10. `src/jarvis/app.py` — Set Google env vars before server starts
Set `GOOGLE_TOKEN_PATH` from settings so handlers can find the token file.

### 11. `src/jarvis/agent/factory.py` — Register gmail + gcal tool modules
```python
from jarvis.tools import file_ops, gcal, gmail, messaging, scheduler_tool, shell, web_search
tool_funcs = collect_tools(shell, web_search, file_ops, messaging, scheduler_tool, gmail, gcal)
```

### 12. `src/jarvis/agent/persona.py` — Add Gmail/GCal instructions
Add section about available Gmail + Calendar capabilities.

### 13. `config/jarvis.yaml` — Add `google:` section
```yaml
google:
  client_secrets_path: "gcp_oauth_client_id.json"
  token_path: "google_token.json"
```

### 14. `.env.example` — Update Google OAuth section
```
GOOGLE_TOKEN_PATH=google_token.json
```

### 15. `pyproject.toml` — Add dependencies
```
google-api-python-client
google-auth-oauthlib
google-auth-httplib2
```

## Tests to Write

### Unit Tests (~26 tests)

**`tests/unit/test_google_auth.py`** (~3 tests)
- `test_loads_token_from_file` — mock token file, verify credentials returned
- `test_refreshes_expired_token` — mock expired credentials, verify refresh called
- `test_raises_when_no_token_file` — no token file → clear error

**`tests/unit/test_gmail_handlers.py`** (~4 tests)
- `test_search_returns_results` — mock Gmail API, verify response shape
- `test_read_returns_email` — mock message.get, verify body decoded
- `test_send_creates_and_sends` — mock send, verify message constructed correctly
- `test_draft_creates_draft` — mock drafts.create, verify draft created

**`tests/unit/test_gcal_handlers.py`** (~4 tests)
- `test_list_returns_events` — mock events.list, verify response shape
- `test_create_event` — mock events.insert, verify event params
- `test_update_event` — mock events.patch, verify partial update
- `test_delete_event` — mock events.delete, verify called

**`tests/unit/test_gmail_tool.py`** (~4 tests)
- `test_gmail_search_calls_bridge` — mock requests.post, verify URL + payload
- `test_gmail_read_calls_bridge` — mock requests.post, verify URL + payload
- `test_gmail_send_calls_bridge` — mock requests.post, verify URL + payload
- `test_gmail_draft_calls_bridge` — mock requests.post, verify URL + payload

**`tests/unit/test_gcal_tool.py`** (~4 tests)
- `test_gcal_list_calls_bridge` — mock requests.post, verify URL + payload
- `test_gcal_create_calls_bridge` — mock requests.post, verify URL + payload
- `test_gcal_update_calls_bridge` — mock requests.post, verify URL + payload
- `test_gcal_delete_calls_bridge` — mock requests.post, verify URL + payload

**`tests/unit/test_http_server.py`** — Add ~4 tests for Google endpoints
- `test_gmail_search_endpoint` — POST to /google/gmail/search, verify handler called
- `test_gmail_send_endpoint` — POST to /google/gmail/send, verify handler called
- `test_gcal_list_endpoint` — POST to /google/gcal/list, verify handler called
- `test_gcal_create_endpoint` — POST to /google/gcal/create, verify handler called

**`tests/unit/test_settings.py`** — Add ~1 test
- `test_loads_google_settings` — verify GoogleSettings from YAML

**`tests/unit/test_factory.py`** — Update existing to include gmail + gcal tools

### Integration Tests (~4 tests)
**`tests/integration/test_google_roundtrip.py`** (requires token + docker)
- `test_gmail_search_real` — search for recent emails
- `test_gcal_list_real` — list today's events
- `test_agent_answers_calendar_question` — ask "what's on my calendar?" → agent uses gcal tool
- `test_agent_searches_email` — ask "search emails from ..." → agent uses gmail tool

## Implementation Order (Strict TDD)

### Step 1: Dependencies
- `uv add google-api-python-client google-auth-oauthlib google-auth-httplib2`

### Step 2: Write ALL tests first (RED phase)
Write every test file. No source files yet.
1. `tests/unit/test_google_auth.py` (3 tests)
2. `tests/unit/test_gmail_handlers.py` (4 tests)
3. `tests/unit/test_gcal_handlers.py` (4 tests)
4. `tests/unit/test_gmail_tool.py` (4 tests)
5. `tests/unit/test_gcal_tool.py` (4 tests)
6. Update `tests/unit/test_http_server.py` (+4 tests)
7. Update `tests/unit/test_settings.py` (+1 test)
8. Update `tests/conftest.py` (add google mock fixtures if needed)
- **Run**: `uv run pytest tests/unit/ -v` → existing 80 pass, ~26 new FAIL (red)

### Step 3: Implement source files (GREEN phase)
Implement one file at a time, running tests after each:
1. `google/__init__.py` + `google/auth.py` → auth tests go green
2. `google/handlers.py` (Gmail) → gmail handler tests go green
3. `google/handlers.py` (Calendar) → gcal handler tests go green
4. `tools/gmail.py` → gmail tool tests go green
5. `tools/gcal.py` → gcal tool tests go green
6. Update `http_server.py` → HTTP endpoint tests go green
7. Update `settings.py` → settings test goes green
8. Update `factory.py`, `persona.py`, `app.py`, `config/jarvis.yaml`, `.env.example`
- **Run**: `uv run pytest tests/unit/ -v` → ALL ~106 green

### Step 4: OAuth setup + integration tests
1. Run `scripts/setup_google_oauth.py` (interactive browser OAuth)
2. Write + run integration tests (with docker compose up + token)

### Step 5: Live verification
- Ask Jarvis on Slack "what's on my calendar today?"
- Ask Jarvis on Slack "search my email for X"

## Validation Gate

- `uv run pytest tests/unit/ -v` — all green (existing 80 + ~26 new = ~106)
- `uv run ruff check src/ tests/` — clean
- `uv run pytest tests/integration/ -v` — all green (with docker compose up + Google token)
- Live Slack: "what's on my calendar today?" → real calendar events returned
- Live Slack: "search my email for X" → real email results returned
