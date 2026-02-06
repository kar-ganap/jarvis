# Phase 1 Plan: Core Loop + CLI Channel

## Goal

Wire the end-to-end message flow: user input → channel → router → Letta agent → response extraction → channel → user output. The CLI channel serves as the dev/testing interface. After this phase, `uv run python -m jarvis` starts an interactive conversation with the agent.

---

## File-by-File Breakdown

### 1. `src/jarvis/channels/__init__.py` — empty

### 2. `src/jarvis/channels/base.py` — Channel ABC + data classes

The foundational types every channel and the router depend on.

```python
from dataclasses import dataclass
from enum import StrEnum
from abc import ABC, abstractmethod
from typing import Callable, Awaitable

class ChannelType(StrEnum):
    CLI = "cli"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    GOOGLE_CHAT = "google_chat"

@dataclass(frozen=True)
class ChannelUser:
    id: str              # channel-specific user ID
    display_name: str    # human-readable name

@dataclass(frozen=True)
class ChannelMessage:
    """Normalized inbound message from any channel."""
    channel_type: ChannelType
    user: ChannelUser
    text: str
    raw: dict | None = None   # original platform payload for debugging

@dataclass(frozen=True)
class OutboundMessage:
    """Message to send back to a channel."""
    channel_type: ChannelType
    recipient_id: str    # channel-specific target (user ID, channel ID, etc.)
    text: str

# Type alias for the callback channels call when a message arrives
InboundHandler = Callable[[ChannelMessage], Awaitable[None]]

class Channel(ABC):
    """Abstract base for all messaging channels."""

    @property
    @abstractmethod
    def channel_type(self) -> ChannelType: ...

    @abstractmethod
    async def start(self, on_message: InboundHandler) -> None:
        """Start listening. Call on_message for each inbound message."""

    @abstractmethod
    async def stop(self) -> None:
        """Graceful shutdown."""

    @abstractmethod
    async def send(self, message: OutboundMessage) -> None:
        """Send an outbound message."""
```

Key decisions:
- `frozen=True` dataclasses — messages are immutable value objects
- `ChannelType` as `StrEnum` — serializes cleanly in logs and prefixes
- `InboundHandler` type alias — channels don't know about the router, they just call a callback
- `raw` field on `ChannelMessage` — preserves original payload for debugging without coupling the interface to any platform

### 3. `src/jarvis/agent/response.py` — Response extraction

Extract the assistant's text reply from a Letta response object.

```python
def extract_assistant_text(response) -> str | None:
    """Extract the assistant's text from a Letta message response.

    Returns the concatenated text of all assistant_message items,
    or None if no assistant message was found.
    """
    texts = []
    for msg in response.messages:
        if msg.message_type == "assistant_message" and msg.content:
            texts.append(msg.content)
    return "\n".join(texts) if texts else None
```

Key decisions:
- Concatenate multiple assistant messages (Letta can return several in one turn if tool calls happen between them)
- Return `None` rather than empty string when no assistant message — caller can decide how to handle

### 4. `src/jarvis/channels/router.py` — MessageRouter

Central hub that connects channels to the Letta agent.

```python
class MessageRouter:
    def __init__(self, client, agent_id: str, channels: dict[ChannelType, Channel]):
        self._client = client
        self._agent_id = agent_id
        self._channels = channels
        self._lock = asyncio.Lock()

    async def handle_inbound(self, message: ChannelMessage) -> None:
        """Process an inbound message: format → send to Letta → reply to channel."""
        # 1. Format with channel prefix: "[cli|UserName] hello"
        prefixed_text = f"[{message.channel_type}|{message.user.display_name}] {message.text}"

        # 2. Send to Letta (serialized — one at a time)
        async with self._lock:
            response = await asyncio.to_thread(
                self._client.agents.messages.create,
                agent_id=self._agent_id,
                messages=[{"role": "user", "content": prefixed_text}],
            )

        # 3. Extract assistant text
        reply_text = extract_assistant_text(response)
        if not reply_text:
            return

        # 4. Send reply back via the originating channel
        outbound = OutboundMessage(
            channel_type=message.channel_type,
            recipient_id=message.user.id,
            text=reply_text,
        )
        channel = self._channels.get(message.channel_type)
        if channel:
            await channel.send(outbound)

    async def send_proactive(self, channel_type: ChannelType, recipient_id: str, text: str) -> None:
        """Send a proactive message (agent-initiated, not in response to user input)."""
        outbound = OutboundMessage(channel_type=channel_type, recipient_id=recipient_id, text=text)
        channel = self._channels.get(channel_type)
        if channel:
            await channel.send(outbound)
```

Key decisions:
- `asyncio.Lock` serializes Letta calls — one message processed at a time, avoids race conditions on agent state
- `asyncio.to_thread` wraps the synchronous Letta SDK call — keeps the event loop responsive
- Channel prefix format `[channel|user]` gives the agent context about where the message came from
- `send_proactive()` is the hook for scheduler/tools to push messages to users (Phase 4)

### 5. `src/jarvis/channels/cli.py` — CLI Channel

Dev/testing channel using stdin/stdout.

```python
class CLIChannel(Channel):
    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.CLI

    async def start(self, on_message: InboundHandler) -> None:
        """Read lines from stdin in a loop, call on_message for each."""
        self._running = True
        user = ChannelUser(id="cli-user", display_name=<user_name_from_settings>)
        while self._running:
            line = await asyncio.to_thread(input, "You: ")
            if line.strip().lower() in ("quit", "exit"):
                break
            msg = ChannelMessage(channel_type=ChannelType.CLI, user=user, text=line.strip())
            await on_message(msg)

    async def stop(self) -> None:
        self._running = False

    async def send(self, message: OutboundMessage) -> None:
        print(f"Jarvis: {message.text}")
```

Key decisions:
- `asyncio.to_thread(input, ...)` — `input()` is blocking, wrapping it keeps the event loop alive
- User name comes from settings (not hardcoded)
- "quit"/"exit" keywords to cleanly stop the loop

### 6. `src/jarvis/app.py` — Application orchestrator

Wires everything together and manages lifecycle.

```python
class JarvisApp:
    def __init__(self, settings: JarvisSettings):
        self.settings = settings
        self._client = None
        self._agent = None
        self._router = None
        self._channels = {}

    async def start(self) -> None:
        """Bootstrap and start the application."""
        # 1. Create Letta client
        # 2. Get or create agent
        # 3. Instantiate channels (CLI for now)
        # 4. Create router
        # 5. Start all channels (passing router.handle_inbound as callback)

    async def stop(self) -> None:
        """Graceful shutdown."""
        # Stop all channels
```

### 7. `src/jarvis/__main__.py` — Entry point

```python
"""Entry point: python -m jarvis"""
import asyncio
from jarvis.app import JarvisApp
from jarvis.settings import load_settings
from jarvis.utils.logging import setup_logging

def main():
    setup_logging()
    settings = load_settings()
    app = JarvisApp(settings)
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
```

---

## Test Plan

### Unit Tests (Mock) — `tests/unit/`

#### `tests/unit/test_response.py`

1. **test_extract_single_assistant_message** — Response with one assistant_message → returns its content
2. **test_extract_multiple_assistant_messages** — Response with two assistant_messages → returns them joined with newline
3. **test_extract_no_assistant_message** — Response with only tool_call/tool_return messages → returns None
4. **test_extract_skips_empty_content** — Assistant message with empty string content → skipped
5. **test_extract_mixed_message_types** — Mix of tool_call, assistant, tool_return → only assistant text extracted

#### `tests/unit/test_router.py`

1. **test_handle_inbound_sends_to_letta** — Verify message is sent to Letta with `[channel|user]` prefix
2. **test_handle_inbound_sends_reply_to_channel** — Verify outbound message is sent back via the correct channel
3. **test_handle_inbound_no_reply_when_no_assistant_text** — When Letta returns no assistant message, channel.send() is NOT called
4. **test_send_proactive** — Verify proactive message is sent to the correct channel

#### `tests/unit/test_cli_channel.py`

1. **test_cli_channel_type** — `channel_type` returns `ChannelType.CLI`
2. **test_cli_send_prints_output** — `send()` prints "Jarvis: <text>" to stdout

#### `tests/unit/test_base.py`

1. **test_channel_message_is_frozen** — Cannot modify fields after creation
2. **test_outbound_message_is_frozen** — Cannot modify fields after creation
3. **test_channel_type_values** — StrEnum values match expected strings

### Integration Tests (Real Letta) — `tests/integration/`

#### `tests/integration/test_message_roundtrip.py`

1. **test_router_roundtrip** — Create real agent, send message through router with a mock channel, verify assistant text comes back via channel.send()

---

## Acceptance Criteria (Validation Gate)

Phase 1 is **complete** when:

1. `uv run pytest tests/unit/ -v` — all unit tests pass (including new Phase 1 tests)
2. `uv run pytest tests/integration/ -v` — all integration tests pass (with docker compose up)
3. `uv run ruff check src/ tests/` — no lint errors
4. `uv run python -m jarvis` — starts interactive CLI conversation, user can type messages and get responses from the agent

---

## Dependencies / Blockers

- Phase 0 complete (Letta server running, agent factory working)
- No new pip dependencies needed — all async primitives are stdlib
