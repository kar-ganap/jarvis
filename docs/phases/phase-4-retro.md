# Phase 4 Retro: Scheduler + Proactive Messaging

## What Worked

- **TDD flow was smooth**: 19 new tests written first (all red), then implemented to green with minimal back-and-forth.
- **aiohttp test_client fixture**: The `pytest-aiohttp` plugin with `aiohttp_client` made HTTP server testing clean — no need to start a real server.
- **Internal HTTP bridge pattern**: Clean separation between Letta sandbox tools (which call HTTP) and the app's in-memory objects (router, scheduler, trigger).
- **Separated `_build_app()` from `start()`**: Made the HTTP server testable without starting a real TCP listener.
- **Live Slack round-trip verified**: "remind me in 1 minute to check the PR" → 1 minute later, notification arrived on Slack.

## Surprises

- **AsyncIOScheduler requires a running event loop at `start()`**: Unit tests are synchronous (no event loop), so `AsyncIOScheduler` failed immediately. Switched to `BackgroundScheduler` with a `_invoke()` wrapper that dispatches async callbacks to the captured event loop via `run_coroutine_threadsafe()`.
- **Trigger notification gap**: The trigger initially only sent a `[scheduler|system]` message to the agent. The agent responded with text, but that response went nowhere (no channel to route back to). Had to add a **dual-path notification**: trigger sends directly via router (reliable) AND informs the agent (for memory). This was the biggest design lesson of the phase.
- **Agent needs routing info**: The agent needs the user's raw channel ID to pass to `create_reminder`'s `notify_channel`/`notify_recipient` params. Updated the message prefix from `[slack|Kartik]` to `[slack|U12345|Kartik]` to include the raw ID.
- **Persona block must be updated on running agent**: Changing `persona.py` only affects new agents. For existing agents, the Letta API (`PATCH /v1/blocks/<id>`) must be called to update the in-context memory block.

## Deviations from Plan

- **BackgroundScheduler instead of AsyncIOScheduler**: More practical — works in sync tests and in production (with async wrapper).
- **Dual-path trigger notification**: Plan had the agent deciding whether to notify. In practice, we send directly via router for reliability and inform the agent for memory. The agent's `send_message_to_user` tool still exists for ad-hoc proactive messaging.
- **Router prefix format changed**: Added user raw ID as second field: `[channel|user_id|display_name]`. This is a cross-cutting change that affects all channels.
- **No dedicated scheduler integration test**: Unit tests cover each component; the live Slack round-trip served as the integration verification.

## Implicit Assumptions Made Explicit

- **`host.docker.internal` for Letta sandbox → host communication**: Letta tools run in Docker, call `http://host.docker.internal:9100`. Works on macOS Docker Desktop. Linux may need `--add-host` flag.
- **APScheduler `MemoryJobStore`**: Dynamic jobs are lost on restart. YAML cron jobs would be re-registered on boot (not yet implemented).
- **Single-user assumption in trigger routing**: The `notify_recipient` comes from whoever set the reminder. Multi-user would need per-job routing stored in the scheduler.
- **Persona block is agent-editable**: The agent can modify its own persona via `memory_replace`. Our scheduler instructions could be overwritten if the agent decides to. Monitoring needed.

## Scope for Next Phase

- Phase 5: Gmail + Google Calendar tools
- Need Google OAuth2 flow, token refresh, Gmail/GCal API wrappers
- Morning briefing cron can be wired to use real Gmail + GCal data

## Numbers

- **Tests**: 80 unit + 9 integration = 89 total (all passing)
- **New tests this phase**: 19 (5 scheduler engine, 2 trigger, 6 HTTP server, 1 messaging tool, 5 scheduler tool)
- **New source files**: 6 (scheduler/__init__.py, engine.py, triggers.py, http_server.py, tools/messaging.py, tools/scheduler_tool.py)
- **Updated source files**: 6 (settings.py, app.py, factory.py, router.py, persona.py, config/jarvis.yaml)
