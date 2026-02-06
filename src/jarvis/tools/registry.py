from __future__ import annotations

from types import ModuleType
from typing import Any

import structlog

log = structlog.get_logger()


def collect_tools(*modules: ModuleType) -> list:
    """Collect all functions listed in each module's TOOLS attribute."""
    tools: list = []
    for mod in modules:
        for func in getattr(mod, "TOOLS", []):
            tools.append(func)
    return tools


def register_tools(client: Any, tool_funcs: list) -> list[str]:
    """Register tool functions with Letta via upsert. Returns list of tool IDs."""
    tool_ids: list[str] = []
    for func in tool_funcs:
        tool = client.tools.upsert_from_function(func=func)
        log.info("tools.registered", name=tool.name, tool_id=tool.id)
        tool_ids.append(tool.id)
    return tool_ids


def sync_agent_tools(client: Any, agent_id: str, tool_ids: list[str]) -> None:
    """Ensure agent has these tools attached."""
    page = client.agents.tools.list(agent_id=agent_id)
    existing = page.items if hasattr(page, "items") else page
    existing_ids = {t.id for t in existing}

    for tid in tool_ids:
        if tid not in existing_ids:
            client.agents.tools.attach(agent_id=agent_id, tool_id=tid)
            log.info("tools.attached", tool_id=tid, agent_id=agent_id)
