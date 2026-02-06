# Phase 3 Plan: Slack Channel

## Goal

Add Slack as the first real messaging channel. Connect via Socket Mode (WebSocket — no public URL needed). Build a channel registry so `app.py` dynamically enables channels from config. After this phase, Jarvis responds to DMs and @mentions on Slack, with tools working.

---

## Slack App Setup (Manual, Pre-Requisite)

Before code, the user must create a Slack app at https://api.slack.com/apps:

1. **Create New App** → From scratch → name "Jarvis", pick workspace
2. **Socket Mode** → Toggle ON → generate App-Level Token (`xapp-*`) with `connections:write` scope
3. **OAuth & Permissions** → Bot Token Scopes:
   - `app_mentions:read` — listen to @mentions
   - `chat:write` — send messages
   - `users:read` — resolve user display names
   - `im:read` — read DMs
   - `im:history` — access DM message history
   - `channels:read` — read channel info
4. **Event Subscriptions** → Toggle ON → Subscribe to bot events:
   - `message.im` — DMs to the bot
   - `app_mention` — @mentions in channels
5. **Install to Workspace** → Copy Bot Token (`xoxb-*`)
6. Add both tokens to `.env`:
   ```
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   ```

---

## File-by-File Breakdown

### 1. `src/jarvis/channels/slack.py` — SlackChannel

```python
from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

class SlackChannel(Channel):
    def __init__(self, bot_token: str, app_token: str):
        self._bot_token = bot_token
        self._app_token = app_token
        self._app: AsyncApp | None = None
        self._handler: AsyncSocketModeHandler | None = None
        self._on_message: InboundHandler | None = None

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.SLACK

    async def start(self, on_message: InboundHandler) -> None:
        self._on_message = on_message
        self._app = AsyncApp(token=self._bot_token)

        # Register message listener (DMs)
        @self._app.message()
        async def handle_message(message, client):
            if message.get("bot_id"):
                return  # ignore bot's own messages
            await self._dispatch(message, client)

        # Register @mention listener
        @self._app.event("app_mention")
        async def handle_mention(event, client):
            if event.get("bot_id"):
                return
            await self._dispatch(event, client)

        self._handler = AsyncSocketModeHandler(
            app=self._app, app_token=self._app_token
        )
        await self._handler.start_async()

    async def _dispatch(self, event: dict, client) -> None:
        """Normalize Slack event → ChannelMessage → call on_message."""
        user_id = event.get("user", "")
        text = event.get("text", "")

        # Resolve display name
        display_name = await self._resolve_user_name(client, user_id)

        msg = ChannelMessage(
            channel_type=ChannelType.SLACK,
            user=ChannelUser(id=event["channel"], display_name=display_name),
            text=text,
            raw=event,
        )
        await self._on_message(msg)

    async def _resolve_user_name(self, client, user_id: str) -> str:
        try:
            info = await client.users_info(user=user_id)
            profile = info["user"]["profile"]
            return profile.get("display_name") or profile.get("real_name") or "User"
        except Exception:
            return "User"

    async def stop(self) -> None:
        if self._handler:
            await self._handler.close_async()

    async def send(self, message: OutboundMessage) -> None:
        """Send a message to a Slack channel."""
        if self._app:
            await self._app.client.chat_postMessage(
                channel=message.recipient_id,
                text=message.text,
            )
```

Key decisions:
- **`recipient_id` = Slack channel ID**: The router sets `recipient_id` to the user's `ChannelUser.id`, which for Slack is the channel ID (DM channel or public channel). This maps directly to `chat_postMessage(channel=...)`.
- **`ChannelUser.id` = channel ID, not user ID**: For Slack, the useful identifier for sending replies is the channel (conversation) ID. User ID is only needed for display name resolution, which we do eagerly on inbound.
- **Bot message filtering**: Check `bot_id` field — present on all bot messages. Prevents infinite loops.
- **`_resolve_user_name`**: Calls `users.info` API to get display name. Falls back to "User" on any error.
- **AsyncApp + AsyncSocketModeHandler**: Full async, runs on the event loop alongside CLI and other channels.

### 2. `src/jarvis/channels/registry.py` — Channel registry

Dynamically creates enabled channels from config. Replaces the hardcoded CLI channel in `app.py`.

```python
class ChannelRegistry:
    @staticmethod
    def build(settings: JarvisSettings) -> dict[ChannelType, Channel]:
        channels: dict[ChannelType, Channel] = {}

        # CLI is always enabled
        channels[ChannelType.CLI] = CLIChannel(user_name=settings.user.name)

        # Slack — enabled if tokens are set
        if settings.slack.enabled:
            channels[ChannelType.SLACK] = SlackChannel(
                bot_token=settings.slack.bot_token,
                app_token=settings.slack.app_token,
            )

        return channels
```

### 3. Update `src/jarvis/settings.py` — Add SlackSettings

```python
class SlackSettings(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    app_token: str = ""

class JarvisSettings(BaseModel):
    letta: LettaSettings = LettaSettings()
    agent: AgentSettings = AgentSettings()
    user: UserSettings = UserSettings()
    slack: SlackSettings = SlackSettings()
```

Tokens come from YAML config (which can reference env vars) or directly from env vars. For simplicity, the YAML can just set `enabled: true` and the tokens come from environment variables.

### 4. Update `config/jarvis.yaml`

```yaml
slack:
  enabled: false
  bot_token: ""   # Override via SLACK_BOT_TOKEN env var
  app_token: ""   # Override via SLACK_APP_TOKEN env var
```

### 5. Update `src/jarvis/app.py` — Use channel registry

Replace hardcoded CLI with registry:

```python
from jarvis.channels.registry import ChannelRegistry

class JarvisApp:
    async def start(self) -> None:
        client = Letta(base_url=self.settings.letta.base_url)
        agent = get_or_create_agent(client, self.settings)

        channels = ChannelRegistry.build(self.settings)

        router = MessageRouter(client=client, agent_id=agent.id, channels=channels)

        # Start all channels concurrently
        tasks = []
        for channel in channels.values():
            tasks.append(asyncio.create_task(
                channel.start(on_message=router.handle_inbound)
            ))
        await asyncio.gather(*tasks)
```

Key change: all channels start concurrently with `asyncio.gather`. CLI blocks on stdin, Slack blocks on WebSocket — both run in parallel.

---

## Test Plan

### Unit Tests (Mock) — `tests/unit/`

#### `tests/unit/test_slack_channel.py`

1. **test_channel_type** — `channel_type` returns `ChannelType.SLACK`
2. **test_normalizes_message_event** — Slack message event dict → `ChannelMessage` with correct fields
3. **test_normalizes_mention_event** — `app_mention` event → `ChannelMessage` with correct fields
4. **test_filters_bot_messages** — Event with `bot_id` field does not call `on_message`
5. **test_send_calls_chat_post_message** — `send()` calls `client.chat_postMessage` with channel and text
6. **test_resolve_user_name_fallback** — When `users.info` fails, falls back to "User"

#### `tests/unit/test_channel_registry.py`

1. **test_always_includes_cli** — Registry always creates CLI channel
2. **test_includes_slack_when_enabled** — When `slack.enabled=True` and tokens set, Slack channel is created
3. **test_excludes_slack_when_disabled** — When `slack.enabled=False`, no Slack channel

#### `tests/unit/test_settings.py` (add to existing)

4. **test_slack_settings_defaults** — Slack settings default to `enabled=False`
5. **test_slack_settings_from_yaml** — Slack settings load from YAML

### Integration Tests (Real Slack) — `tests/integration/`

Integration tests for Slack require a real Slack workspace and bot tokens. We'll mark them to skip if tokens aren't set.

#### `tests/integration/test_slack_connection.py`

1. **test_socket_mode_connects** — AsyncSocketModeHandler connects and doesn't error (smoke test)

---

## Acceptance Criteria (Validation Gate)

Phase 3 is **complete** when:

1. `uv run pytest tests/unit/ -v` — all unit tests pass
2. `uv run pytest tests/integration/ -v` — all integration tests pass
3. `uv run ruff check src/ tests/` — no lint errors
4. DM the bot on Slack → get a response from the agent (manual test)
5. @mention the bot in a channel → get a response (manual test)
6. Tools work from Slack (e.g., "run the command: echo hello") (manual test)

---

## Dependencies

```bash
uv add slack-bolt aiohttp
```

Add to `.env.example`:
```
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
```

Add to `.env`:
```
SLACK_BOT_TOKEN=<real token>
SLACK_APP_TOKEN=<real token>
```
