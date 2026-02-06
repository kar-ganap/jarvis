# Phase 5 Retro: Gmail + Google Calendar

## What Worked

- **TDD flow was clean**: 24 new tests written first (all red), implemented to green incrementally with no major surprises. Smooth progression: auth → handlers → tools → HTTP routes → settings.
- **HTTP bridge pattern scales well**: Same pattern from Phase 4 (scheduler tools → HTTP → app logic) extended naturally to 8 new Google endpoints. No architectural changes needed.
- **Google API integration was straightforward**: `google-api-python-client` with OAuth2 desktop flow worked out of the box. Token auto-refresh handled transparently.
- **Live Slack verification was flawless**: "what's on my calendar today?" returned real events, "what's the latest email" returned real email content — both on first try, no debugging needed.
- **OAuth setup script**: One-time `scripts/setup_google_oauth.py` → browser auth → token saved. Clean developer experience.

## Surprises

- **GCP OAuth consent screen "Internal" vs "External"**: The OAuth app was initially set to "Internal" (Workspace-only), which blocked personal Google accounts. Fixed by switching to "External" with test user. Worth noting for anyone setting up a fresh GCP project.
- **Letta tool pagination**: Adding 8 new tools (4 Gmail + 4 GCal) pushed the agent's total tool count past the default page size for `agents.tools.list()`. The existing `test_register_and_attach_tools` integration test failed because `execute_shell_command` wasn't on the first page. Fixed by adding `limit=100` to the list call.
- **No code-level debugging needed**: Unlike Phase 4 (which required discovering and fixing the trigger notification gap), this phase had zero implementation bugs. The HTTP bridge pattern was proven and the Google API client is well-documented.

## Deviations from Plan

- **24 tests instead of 26**: The plan estimated ~26 unit tests. We landed on 24 (3 auth + 4 gmail handlers + 4 gcal handlers + 4 gmail tools + 4 gcal tools + 4 HTTP endpoints + 1 settings). The factory test update was unnecessary since the existing tests already cover tool registration generically.
- **Handler functions are plain functions, not aiohttp handlers**: The plan described handlers as `handle_gmail_search(request)` but we implemented them as pure functions (`gmail_search(query, max_results)`) called from the HTTP server via `asyncio.to_thread()`. Cleaner separation — handlers know nothing about HTTP.
- **3 integration tests instead of 4**: Skipped the "agent answers calendar question" and "agent searches email" integration tests (those are effectively covered by the live Slack verification). Wrote 3 focused tests: gmail search, gmail read, gcal list.

## Implicit Assumptions Made Explicit

- **Token file at project root**: `google_token.json` lives at the project root (gitignored). The `GOOGLE_TOKEN_PATH` env var can override this, but the default assumes running from the project directory.
- **`gmail.modify` scope**: We use `gmail.modify` (not `gmail.readonly`) to support send and draft operations. This is broader than needed for read-only use.
- **`calendar.events` scope**: Covers list/create/update/delete for events on the primary calendar only. Doesn't access other calendars or settings.
- **Google API calls are synchronous**: Handlers use `googleapiclient` which is synchronous. The HTTP server wraps them in `asyncio.to_thread()` to avoid blocking the event loop. Fine for single-user, but would need connection pooling for multi-user.
- **No rate limiting**: Google APIs have quotas. We don't implement any client-side rate limiting or retry logic. For personal use this is fine.

## Scope for Next Phase

- Phase 6: WhatsApp Channel (Node.js Baileys bridge)
- Cross-channel memory verification (tell on Slack, ask on WhatsApp)

## Numbers

- **Tests**: 104 unit + 12 integration = 116 total (all passing)
- **New tests this phase**: 24 unit + 3 integration = 27
- **New source files**: 5 (google/__init__.py, google/auth.py, google/handlers.py, tools/gmail.py, tools/gcal.py)
- **New script**: 1 (scripts/setup_google_oauth.py)
- **Updated source files**: 7 (http_server.py, settings.py, factory.py, persona.py, app.py, config/jarvis.yaml, .env.example)
- **Updated test files**: 3 (test_http_server.py, test_settings.py, test_tool_registration.py)
