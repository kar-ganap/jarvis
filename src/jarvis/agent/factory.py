from __future__ import annotations

import structlog

from jarvis.agent.persona import build_human_block, build_persona_block
from jarvis.settings import JarvisSettings
from jarvis.tools import (
    browser,
    file_ops,
    gcal,
    gmail,
    gslides,
    messaging,
    notion,
    scheduler_tool,
    shell,
    web_search,
)
from jarvis.tools.registry import collect_tools, register_tools, sync_agent_tools

log = structlog.get_logger()


def get_or_create_agent(client, settings: JarvisSettings):
    """Get an existing agent by name, or create a new one.

    Idempotent: calling twice with the same settings returns the same agent.
    """
    name = settings.agent.name

    # Register tools with Letta (idempotent)
    tool_funcs = collect_tools(
        shell, web_search, file_ops, messaging, scheduler_tool,
        gmail, gcal, gslides, notion, browser,
    )
    tool_ids = register_tools(client, tool_funcs)

    page = client.agents.list(name=name)
    # Handle both paginated (real client) and plain list (mock) returns
    existing = page.items if hasattr(page, "items") else page
    if existing:
        log.info("agent.found_existing", name=name, agent_id=existing[0].id)
        sync_agent_tools(client, existing[0].id, tool_ids)
        return existing[0]

    persona_text = build_persona_block(agent_name=name)
    human_text = build_human_block(user_name=settings.user.name)

    agent = client.agents.create(
        name=name,
        model=settings.agent.model,
        embedding=settings.agent.embedding,
        context_window_limit=settings.agent.context_window_limit,
        memory_blocks=[
            {
                "label": "persona",
                "value": persona_text,
                "description": "The agent's identity, capabilities, and behavioral guidelines.",
            },
            {
                "label": "human",
                "value": human_text,
                "description": "Information about the user — preferences, context, and history.",
            },
        ],
        tool_ids=tool_ids,
        include_base_tools=True,
    )

    log.info("agent.created", name=name, agent_id=agent.id)
    return agent
