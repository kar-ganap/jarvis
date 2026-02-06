# Phase 6 Retro: WhatsApp Channel

## What Worked

- **Two-service architecture was clean**: Node.js Baileys bridge as a separate Docker container with REST API, Python WhatsAppChannel talking to it over HTTP. Clean separation — bridge handles WhatsApp protocol, Python handles Jarvis integration.
- **Channel ABC pattern scales well**: WhatsAppChannel followed the exact same interface as SlackChannel. Registry, router, and messaging tool required minimal changes — they're truly channel-agnostic.
- **Webhook push model was simpler than expected**: Unlike Slack (Socket Mode, pull), WhatsApp uses bridge → webhook push. The `dispatch_webhook()` method on the channel class + HTTP endpoint was straightforward.
- **Cross-channel messaging worked on first try**: WhatsApp user asked Jarvis to send a message on Slack — delivered correctly. Slack→WhatsApp memory test also passed (told something on Slack, asked on WhatsApp, remembered).
- **Proactive messaging worked**: Reminder set on Slack with `notify_channel=whatsapp` delivered on WhatsApp.

## Surprises

- **Baileys auth state on logout**: After logging out from WhatsApp, the bridge kept retrying with stale auth (401 loop) instead of showing a new QR. The Docker volume mount meant we couldn't `rmSync` the auth directory (EBUSY). Fixed by clearing directory *contents* instead of the directory itself.
- **`source .env` doesn't export**: `source .env` loads variables but doesn't export them to child processes. Need `set -a && source .env && set +a` for `uv run` to pick them up.
- **Agent leaked internal IDs**: When asked to send a cross-channel message, the agent exposed the Slack DM channel ID (D0ADBE4NC4D) to the WhatsApp user. Fixed by adding a PRIVACY section to the persona block instructing the agent to never expose internal identifiers.
- **Baileys `no name present` warning**: Harmless pino warning from Baileys when it can't resolve a contact's name from presence updates. Doesn't affect message delivery.

## Deviations from Plan

- **14 unit tests instead of planned 14**: Landed exactly on plan. The `test_excludes_whatsapp_when_disabled` test passes with existing code (no WhatsApp in default settings), so it passed from the start — not a failure in the RED phase.
- **Added PRIVACY persona section**: Not in the original plan. Discovered during live testing when the agent leaked Slack IDs to WhatsApp users.
- **Added `.gitignore` entries**: `node_modules/` and `bridge/whatsapp/auth_data/` not in original plan but necessary.

## Implicit Assumptions Made Explicit

- **Bridge runs on port 9120**: Configurable via `WHATSAPP_BRIDGE_PORT` env var, defaults to 9120.
- **Webhook URL uses `host.docker.internal`**: Bridge inside Docker calls back to Jarvis on the host. Works on macOS/Windows Docker Desktop. Linux may need `--add-host` or network mode adjustment.
- **DMs only by default**: Group messages filtered by `_should_skip()`. Configurable via `allow_groups` in settings.
- **Text only**: Media messages with captions forward the caption with `[media: type]` prefix. Media-only messages are skipped.
- **WhatsApp JID as user ID**: Format is `919876543210@s.whatsapp.net`. Used for routing replies back to the correct chat.
- **Bridge handles rate limiting**: 1-second delay between sends on the bridge side. Python side has single retry with 2-second backoff.
- **Session persistence**: Auth state in Docker volume (`whatsapp_auth`). Survives restarts, lost on `docker compose down -v`.

## Scope for Next Phase

- Phase 7: Browser + Notion (+ possibly Google Slides)

## Numbers

- **Tests**: 118 unit + 14 integration = 132 total (all passing)
- **New tests this phase**: 14 unit + 2 integration = 16
- **New source files**: 1 Python (`channels/whatsapp.py`) + 5 Node.js (`bridge/whatsapp/`)
- **Modified source files**: 7 (`settings.py`, `registry.py`, `http_server.py`, `app.py`, `persona.py`, `messaging.py`, `jarvis.yaml`)
- **Modified config/infra**: 3 (`docker-compose.yml`, `.env.example`, `.gitignore`)
