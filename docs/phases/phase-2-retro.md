# Phase 2 Retro: First Tools (Shell + Web Search + File Ops)

## What Worked
- TDD flow continues to be effective — 21 new unit tests written first (all red), implementation made them green in one pass
- Tool registry pattern is simple and explicit — `TOOLS = [func]` list per module, no magic decorators
- `upsert_from_function` is truly idempotent — safe to call on every startup, handles creates and updates
- `sync_agent_tools` handles the Phase 0/1 → Phase 2 transition cleanly — agents created before tools existed get tools attached automatically
- Shell tool env filtering works correctly — sensitive vars are stripped from subprocess environment
- Mock fixture update in conftest.py (adding `upsert_from_function` side_effect) was sufficient — no test fragility

## Surprises
- **Letta schema generation rejects `str | None`**: The `execute_shell_command(workdir: str | None = None)` signature failed with `"Python type str | None has no corresponding JSON schema type"`. Letta's sandbox serializer only supports primitive types (`int`, `str`, `bool`, `float`, `None`), not union types. Fixed by changing to `workdir: str = ""` and treating empty string as None internally.
- **No other surprises**: The Letta tool API worked exactly as documented. `upsert_from_function` extracts source via `inspect.getsource()`, and `agents.tools.attach()` is clean.

## Deviations from Plan
- **Tavily instead of Brave Search**: User chose Tavily as the search provider. Tavily is purpose-built for AI agents and returns pre-processed, LLM-friendly results with `include_answer`.
- **Type hint constraint**: `str | None` → `str = ""` for Letta sandbox compatibility. This is a hard constraint that applies to all future tools.

## Assumptions Made Explicit
- Letta tool functions must use only primitive type hints (`str`, `int`, `bool`, `float`) — no union types, no Optional, no complex types
- All imports must be inside the function body (Letta serializes source code)
- `requests` is available in Letta's sandbox environment (no pip_requirements needed)
- Env vars set in Docker `.env` are available to Letta sandbox tools via `os.environ`
- Tool registration via `upsert_from_function` is safe to call on every startup — idempotent

## Scope Changes for Next Phase
- No additions or removals

## Key Decisions and Rationale
- **Module-level `TOOLS` list**: Explicit over implicit. Each module declares what it exports. No scan-and-discover magic.
- **`requests.post` for Tavily (no SDK)**: Letta sandbox can't import arbitrary packages. Raw HTTP with `requests` is simpler and guaranteed available.
- **Empty string default instead of None**: Letta's schema generator can't handle union types. Using `str = ""` with empty-string-as-None is the pragmatic workaround.
- **Env filtering by keyword**: Strips any env var containing KEY/SECRET/TOKEN/PASSWORD/CREDENTIAL. Broad but safe — prevents credential leakage in shell output.

## Metrics
- New tests: 23 unit + 3 integration (all passing)
- Total tests: 50 unit + 8 integration = 58 (all passing)
- New files: 5 source + 5 test = 10
- Modified files: 3 (factory.py, conftest.py, .env.example)
- Lint: clean
