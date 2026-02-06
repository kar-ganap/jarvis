# Phase 2 Plan: First Tools (Shell + Web Search + File Ops)

## Goal

Give the agent hands. Register custom tools with Letta so the agent can execute shell commands, search the web (Tavily), and read/write files. After this phase, the agent autonomously decides when to use tools based on the conversation.

---

## File-by-File Breakdown

### 1. `src/jarvis/tools/__init__.py` — empty

### 2. `src/jarvis/tools/registry.py` — Tool registration

Collects tool functions from tool modules and registers them with Letta via `upsert_from_function`. Returns tool IDs for attachment to the agent.

```python
import inspect
import structlog
from types import ModuleType

log = structlog.get_logger()

# Each tool module exposes a TOOLS list of functions
def collect_tools(*modules: ModuleType) -> list[callable]:
    """Collect all functions listed in each module's TOOLS attribute."""
    tools = []
    for mod in modules:
        for func in getattr(mod, "TOOLS", []):
            tools.append(func)
    return tools

def register_tools(client, tool_funcs: list[callable]) -> list[str]:
    """Register tool functions with Letta via upsert. Returns list of tool IDs."""
    tool_ids = []
    for func in tool_funcs:
        tool = client.tools.upsert_from_function(func=func)
        log.info("tools.registered", name=tool.name, tool_id=tool.id)
        tool_ids.append(tool.id)
    return tool_ids

def sync_agent_tools(client, agent_id: str, tool_ids: list[str]) -> None:
    """Ensure agent has exactly these tools attached (plus Letta base tools)."""
    # List currently attached tools
    page = client.agents.tools.list(agent_id=agent_id)
    existing = page.items if hasattr(page, "items") else page
    existing_ids = {t.id for t in existing}

    for tid in tool_ids:
        if tid not in existing_ids:
            client.agents.tools.attach(agent_id=agent_id, tool_id=tid)
            log.info("tools.attached", tool_id=tid, agent_id=agent_id)
```

Key decisions:
- **Module-level `TOOLS` list**: Each tool module exports a `TOOLS = [func1, func2]` list. Simple, explicit, no magic decorators.
- **`upsert_from_function`**: Idempotent — safe to call on every startup. If source code changed, tool is updated.
- **`sync_agent_tools`**: Attaches missing tools to an existing agent. Handles the case where the agent was created in a previous phase without tools.

### 3. `src/jarvis/tools/shell.py` — Shell execution

```python
def execute_shell_command(command: str, workdir: str | None = None) -> str:
    """Execute a shell command and return the output.

    Args:
        command: The shell command to execute.
        workdir: Optional working directory. Defaults to home directory.

    Returns:
        A string with stdout, stderr, and exit code.
    """
    import subprocess
    import os

    workdir = workdir or os.path.expanduser("~")

    # Filter sensitive env vars
    env = {k: v for k, v in os.environ.items()
           if not any(secret in k.upper() for secret in
                      ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL"))}

    result = subprocess.run(
        command, shell=True, capture_output=True, text=True,
        timeout=30, cwd=workdir, env=env,
    )

    parts = []
    if result.stdout:
        parts.append(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        parts.append(f"STDERR:\n{result.stderr}")
    parts.append(f"EXIT CODE: {result.returncode}")
    return "\n".join(parts)

TOOLS = [execute_shell_command]
```

Key decisions:
- **Env filtering**: Strips any env var containing KEY, SECRET, TOKEN, PASSWORD, CREDENTIAL from the subprocess environment. Prevents accidental credential leakage in command output.
- **30s timeout**: Prevents runaway commands from blocking the agent forever.
- **Shell=True**: Allows piping, redirects, etc. Acceptable because the agent is a personal assistant on a personal machine, not a multi-tenant service.

### 4. `src/jarvis/tools/web_search.py` — Tavily search

```python
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information using Tavily.

    Args:
        query: The search query.
        max_results: Number of results to return (1-10). Defaults to 5.

    Returns:
        A formatted string with search results including titles, URLs, and snippets.
    """
    import os
    import requests

    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "ERROR: TAVILY_API_KEY not set."

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": min(max_results, 10),
            "include_answer": True,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    parts = []
    if data.get("answer"):
        parts.append(f"Summary: {data['answer']}\n")
    for i, r in enumerate(data.get("results", []), 1):
        parts.append(f"{i}. {r['title']}\n   {r['url']}\n   {r.get('content', '')[:200]}")

    return "\n\n".join(parts) if parts else "No results found."

TOOLS = [web_search]
```

Key decisions:
- **Direct `requests.post`**: No Tavily SDK needed. The REST API is simple — one POST endpoint. Avoids adding a dependency that wouldn't be available in Letta's sandbox.
- **`include_answer: True`**: Tavily returns an AI-generated summary alongside results — useful for the agent to reason about.
- **Content truncation**: Snippets limited to 200 chars to keep context window usage reasonable.

### 5. `src/jarvis/tools/file_ops.py` — File operations

```python
def read_file(path: str) -> str:
    """Read the contents of a text file.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        The file contents, or an error message if the file cannot be read.
    """
    import os

    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)

    if not os.path.exists(path):
        return f"ERROR: File not found: {path}"

    with open(path, "r") as f:
        content = f.read()

    if len(content) > 10000:
        return content[:10000] + f"\n\n[TRUNCATED — file is {len(content)} chars total]"
    return content


def write_file(path: str, content: str) -> str:
    """Write content to a text file. Creates parent directories if needed.

    Args:
        path: Absolute or relative path to the file.
        content: The text content to write.

    Returns:
        A confirmation message or error.
    """
    import os

    if not os.path.isabs(path):
        path = os.path.join(os.path.expanduser("~"), path)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

    return f"OK: Wrote {len(content)} chars to {path}"


def list_directory(path: str = "~") -> str:
    """List the contents of a directory.

    Args:
        path: Directory path. Defaults to home directory.

    Returns:
        A formatted listing of files and directories.
    """
    import os

    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return f"ERROR: Not a directory: {path}"

    entries = sorted(os.listdir(path))
    lines = []
    for entry in entries[:100]:  # cap at 100 entries
        full = os.path.join(path, entry)
        suffix = "/" if os.path.isdir(full) else ""
        lines.append(f"  {entry}{suffix}")

    header = f"Contents of {path} ({len(entries)} items):"
    if len(entries) > 100:
        lines.append(f"  ... and {len(entries) - 100} more")
    return header + "\n" + "\n".join(lines)


TOOLS = [read_file, write_file, list_directory]
```

Key decisions:
- **Relative paths resolve to home dir**: Safe default — the agent's "workspace" is the user's home directory.
- **10KB read truncation**: Prevents enormous files from blowing up the context window.
- **100 entry directory cap**: Same reasoning — don't flood the agent with thousands of filenames.
- **No workspace scoping yet**: Phase 9 will add proper sandboxing. For now, the agent can read/write anywhere — acceptable for a personal assistant on a personal machine.

### 6. Update `src/jarvis/agent/factory.py` — Wire tools into agent creation

The factory needs to:
1. Import tool modules
2. Call `collect_tools()` to gather all tool functions
3. Call `register_tools()` to upsert them with Letta and get IDs
4. Pass `tool_ids` to `agents.create()` for new agents
5. Call `sync_agent_tools()` for existing agents (to add tools created after the agent)

```python
# In get_or_create_agent():
from jarvis.tools import shell, web_search, file_ops
from jarvis.tools.registry import collect_tools, register_tools, sync_agent_tools

tool_funcs = collect_tools(shell, web_search, file_ops)
tool_ids = register_tools(client, tool_funcs)

if existing_agent:
    sync_agent_tools(client, existing_agent.id, tool_ids)
    return existing_agent
else:
    agent = client.agents.create(..., tool_ids=tool_ids)
    return agent
```

### 7. Update `config/jarvis.yaml` and `src/jarvis/settings.py`

Add `TAVILY_API_KEY` to `.env.example`. No new YAML config needed — the API key is an environment variable read inside the sandbox, not a Jarvis setting.

---

## Test Plan

### Unit Tests (Mock) — `tests/unit/`

#### `tests/unit/test_registry.py`

1. **test_collect_tools_from_modules** — `collect_tools(mod1, mod2)` returns combined list of functions from each module's `TOOLS` attribute
2. **test_collect_tools_skips_module_without_tools** — Module without `TOOLS` attribute is safely skipped
3. **test_register_tools_calls_upsert** — Each function is registered via `client.tools.upsert_from_function(func=func)`, returns list of tool IDs
4. **test_sync_agent_tools_attaches_missing** — Tools not yet attached to agent are attached via `client.agents.tools.attach()`
5. **test_sync_agent_tools_skips_existing** — Tools already attached are not re-attached

#### `tests/unit/test_shell.py`

1. **test_execute_returns_stdout** — Successful command returns stdout and exit code 0
2. **test_execute_returns_stderr** — Failed command returns stderr and non-zero exit code
3. **test_execute_filters_env** — Env vars containing KEY/SECRET/TOKEN/PASSWORD/CREDENTIAL are filtered out
4. **test_execute_timeout** — Command exceeding timeout raises/returns timeout error
5. **test_execute_custom_workdir** — Command runs in specified working directory

#### `tests/unit/test_web_search.py`

1. **test_search_formats_results** — Successful Tavily response is formatted with titles, URLs, snippets
2. **test_search_includes_answer** — When Tavily returns an `answer`, it's included at the top
3. **test_search_missing_api_key** — Returns error string when TAVILY_API_KEY not set
4. **test_search_handles_empty_results** — Returns "No results found" when results list is empty

#### `tests/unit/test_file_ops.py`

1. **test_read_file_returns_content** — Reads file and returns contents
2. **test_read_file_not_found** — Returns error for nonexistent file
3. **test_read_file_truncates_large** — Files over 10KB are truncated with message
4. **test_write_file_creates** — Creates file with content, returns confirmation
5. **test_write_file_creates_dirs** — Creates parent directories if needed
6. **test_list_directory** — Returns formatted listing with files and dirs
7. **test_list_directory_caps_at_100** — Directories with >100 entries are capped

#### `tests/unit/test_factory.py` (update existing)

8. **test_creates_agent_with_tool_ids** — New agent is created with `tool_ids` param
9. **test_syncs_tools_for_existing_agent** — Existing agent gets tools synced

### Integration Tests (Real Letta) — `tests/integration/`

#### `tests/integration/test_tool_registration.py`

1. **test_register_and_attach_tools** — Register shell tool with real Letta, attach to agent, verify it appears in agent's tool list
2. **test_agent_calls_shell_tool** — Ask agent "run the command: echo hello" → agent uses `execute_shell_command` → response contains "hello"

---

## Acceptance Criteria (Validation Gate)

Phase 2 is **complete** when:

1. `uv run pytest tests/unit/ -v` — all unit tests pass
2. `uv run pytest tests/integration/ -v` — all integration tests pass (with docker compose up)
3. `uv run ruff check src/ tests/` — no lint errors
4. `uv run python -m jarvis` → ask "what's in my home directory?" → agent calls `list_directory` or `execute_shell_command("ls")` and responds with actual contents

---

## Dependencies

```bash
uv add requests   # For Tavily HTTP calls in tool sandbox
```

Add to `.env.example`:
```
TAVILY_API_KEY=tvly-your-key-here
```

Add to `.env` (for Docker / Letta sandbox):
```
TAVILY_API_KEY=<real key>
```
