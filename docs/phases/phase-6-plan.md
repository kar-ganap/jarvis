# Phase 6: WhatsApp Channel — Implementation Plan

## Architecture

Two-service design:

1. **Node.js Baileys Bridge** (`bridge/whatsapp/`) — Docker container managing WhatsApp Web connection via Baileys. REST API for outbound, webhook push for inbound.
2. **Python WhatsAppChannel** (`src/jarvis/channels/whatsapp.py`) — Channel ABC implementation that talks to the bridge over HTTP.

```
INBOUND:  WhatsApp → Baileys bridge → POST /whatsapp/inbound (Jarvis HTTP) → router → Letta
OUTBOUND: Letta → router → WhatsAppChannel.send() → POST /send (bridge) → WhatsApp
```

Key difference from Slack: Slack uses Socket Mode (pulls via WebSocket). WhatsApp uses webhook push (bridge pushes to Jarvis HTTP server). `WhatsAppChannel.start()` does NOT block — stores callback, health-checks bridge. HTTP server's `/whatsapp/inbound` receives messages and calls `channel.dispatch_webhook(data)`.

## Scope Decisions

- **Text only** for Phase 6. Media with captions → forward caption with `[media: type]` prefix. Media-only → skip.
- **DMs only** by default. Group messages filtered by `_should_skip()`. Configurable via `allow_groups`.
- **No rate limiting** on Python side — bridge handles 1s delay between sends.
- **WhatsApp formatting**: Raw text passed through. Persona instructs agent to use `*bold*`, `_italic_`.

## Files to Create (8)

### 1-5. `bridge/whatsapp/` — Node.js Baileys Bridge

- `package.json` — Deps: `@whiskeysockets/baileys`, `express`, `pino`, `qrcode-terminal`
- `src/index.js` — Entry point (env config, Express + Baileys init)
- `src/session.js` — Baileys socket, QR auth, reconnect, message listener
- `src/routes.js` — Express routes: /health, /send
- `Dockerfile` — node:20-alpine, expose 9120

### 6. `src/jarvis/channels/whatsapp.py` — WhatsAppChannel class
### 7. `tests/unit/test_whatsapp_channel.py` — 8 unit tests
### 8. `tests/integration/test_whatsapp_bridge.py` — 2 integration tests

## Files to Modify (9)

1. `src/jarvis/settings.py` — Add WhatsAppSettings
2. `src/jarvis/channels/registry.py` — Add WhatsApp construction
3. `src/jarvis/http_server.py` — Add /whatsapp/inbound webhook
4. `src/jarvis/app.py` — Pass whatsapp_channel to InternalServer
5. `src/jarvis/agent/persona.py` — Add WHATSAPP section
6. `src/jarvis/tools/messaging.py` — Update docstring
7. `config/jarvis.yaml` — Add whatsapp section
8. `docker-compose.yml` — Add whatsapp_bridge service
9. `.env.example` — Add WHATSAPP_BRIDGE_URL

## Test Plan (~14 unit + 2 integration = 16 new tests)

- `test_whatsapp_channel.py` (8): channel_type, start, send, retry, dispatch, skip logic
- `test_http_server.py` (+2): webhook dispatch, 404 when unconfigured
- `test_channel_registry.py` (+2): includes/excludes whatsapp
- `test_settings.py` (+1): loads WhatsAppSettings
- `test_persona.py` (+1): includes WHATSAPP section
- `test_whatsapp_bridge.py` (2): bridge health, webhook roundtrip

## Implementation Order (Strict TDD)

1. Branch + plan doc
2. Write ALL tests (RED) → verify 104 pass, ~14 fail
3. Implement Python source (GREEN) → all ~118 green
4. Build Node.js bridge
5. Docker compose + QR auth
6. Integration tests + live verification

## Validation Gate

- `uv run pytest tests/unit/ -v` — all ~118 green
- `uv run ruff check src/ tests/` — clean
- Integration tests passing with bridge
- Live: WhatsApp DM → reply, cross-channel Slack ↔ WhatsApp
