# Phase 1 Retro: Core Loop + CLI Channel

## What Worked
- TDD flow was smooth again — 14 new unit tests written first (all red), implementation made them green in one pass
- Channel ABC design proved clean — `CLIChannel` implementation was trivial, which is a good sign for future channels
- `InboundHandler` callback pattern decouples channels from the router — channels don't know about `MessageRouter`
- `asyncio.to_thread` wrapping for both `input()` and Letta SDK calls keeps the event loop responsive without complexity
- Integration test (`test_router_roundtrip`) with a mock channel against real Letta confirmed the full flow works end-to-end
- Response extraction handles edge cases well — multiple assistant messages, empty content, mixed message types

## Surprises
- **Ruff import ordering**: `collections.abc` must come before `dataclasses` alphabetically. Ruff's isort rules are strict about stdlib import ordering within a block.
- **No new surprises with Letta**: The SDK behaved exactly as expected from Phase 0 research. `client.agents.messages.create()` returns a response with `.messages` list containing typed objects with `.message_type` and `.content` — all documented in Phase 0.

## Deviations from Plan
- None. All 7 files created exactly as planned. All tests match the plan's test matrix.

## Assumptions Made Explicit
- Letta response messages always have `.message_type` and `.content` attributes — the SDK returns typed objects, not dicts
- `asyncio.Lock` is sufficient for serializing agent calls in a single-process app — no need for distributed locking
- `ChannelMessage.raw` field (optional dict for original platform payload) is included in the type but not used by CLI — will be useful for Slack/WhatsApp debugging in later phases

## Scope Changes for Next Phase
- No additions or removals

## Key Decisions and Rationale
- **`frozen=True` dataclasses**: Messages are immutable value objects. Prevents accidental mutation as they flow through router → agent → channel. Worth the minor inconvenience of no in-place updates.
- **`StrEnum` for ChannelType**: Serializes to clean strings in logs (`cli`, `slack`) rather than numeric enum values. Makes structured logs human-readable.
- **Channel prefix format `[channel|user]`**: Simple, parseable, gives the agent context about message origin. The agent sees `[cli|Kartik] hello` and can reason about which channel to reply on.
- **`send_proactive()` on router**: Included now as a forward-looking hook for Phase 4 (scheduler/proactive messaging). Zero cost to add, avoids refactoring later.

## Metrics
- New tests: 14 unit + 1 integration (all passing)
- Total tests: 27 unit + 5 integration = 32 (all passing)
- New files: 7 source + 5 test = 12
- Lint: clean (ruff check passes)
