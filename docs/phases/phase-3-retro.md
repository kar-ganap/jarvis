# Phase 3 Retro: Slack Channel

## What Worked
- Channel ABC from Phase 1 paid off — `SlackChannel` implements the same interface as `CLIChannel`, zero changes needed in the router
- Socket Mode connection was straightforward — `AsyncSocketModeHandler` connects via WebSocket, no public URL needed
- `ChannelRegistry` cleanly separates channel instantiation from the app orchestrator — `app.py` no longer hardcodes channels
- Env var fallback for tokens works well — YAML sets `enabled: true`, tokens come from environment variables, no secrets in git
- `asyncio.gather` starts CLI + Slack concurrently — both channels active at the same time
- Manual test worked on first try — DM to bot on Slack got a response from the agent with correct display name
- Tools work from Slack — agent can call shell, web search, file ops when asked via Slack DMs

## Surprises
- **No real surprises** — Slack Socket Mode with slack-bolt is well-documented and worked as expected
- **Display name confusion**: Initially thought the bot was processing its own messages because the resolved display name was "Jarvis, Kartik's Personal AI Assistant" — turned out that was the user's Slack workspace profile name, not the bot's
- **`ssl=None` deprecation warning**: slack-sdk's aiohttp WebSocket connection emits `DeprecationWarning: ssl=None is deprecated` — cosmetic, not functional

## Deviations from Plan
- **Added `subtype` filtering**: Plan only mentioned `bot_id` filtering. Added `subtype` check for `bot_message`, `message_changed`, `message_deleted` as defensive measure
- **Env var fallback in settings**: Plan didn't specify how tokens flow from env vars. Added fallback logic in `load_settings()` — if YAML token is empty, reads from `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` env vars

## Assumptions Made Explicit
- Slack tokens should come from environment variables, not YAML config (to avoid committing secrets)
- `event["channel"]` is the right identifier for `ChannelUser.id` in Slack — it maps directly to `chat_postMessage(channel=...)` for replies
- `users.info` API is the way to resolve display names — may need caching if it becomes a bottleneck
- `AsyncSocketModeHandler.start_async()` blocks (keeps WebSocket alive) — must run concurrently with other channels via `asyncio.gather`

## Scope Changes for Next Phase
- No additions or removals

## Key Decisions and Rationale
- **`ChannelUser.id` = channel ID for Slack**: The conversation/channel ID (not user ID) is what's needed to send replies. This keeps the router generic — it just passes `recipient_id` to `channel.send()`.
- **Registry pattern**: Static `build()` method on `ChannelRegistry` — simple, testable, no runtime discovery magic. Future channels (WhatsApp, Google Chat) just add another `if settings.X.enabled` block.
- **Env var fallback, not override**: YAML values take precedence if set. Empty string in YAML falls back to env var. This lets users choose where to put secrets.

## Metrics
- New tests: 11 unit + 1 integration (all passing)
- Total tests: 61 unit + 9 integration = 70 (all passing, 1 skipped without tokens)
- New files: 4 source + 3 test = 7
- Modified files: 4 (settings.py, app.py, jarvis.yaml, .env.example)
- Lint: clean
- Manual test: Slack DM roundtrip verified
