from __future__ import annotations

import pytest


class TestToolRegistration:
    def test_register_and_attach_tools(self):
        """Register shell tool with real Letta, attach to agent, verify it appears."""
        from letta_client import Letta

        from jarvis.settings import load_settings
        from jarvis.tools.registry import register_tools, sync_agent_tools
        from jarvis.tools.shell import execute_shell_command

        settings = load_settings()
        client = Letta(base_url=settings.letta.base_url)

        # Register the shell tool
        tool_ids = register_tools(client, [execute_shell_command])
        assert len(tool_ids) == 1

        # Get or create test agent
        from jarvis.agent.factory import get_or_create_agent

        agent = get_or_create_agent(client, settings)

        # Sync tools
        sync_agent_tools(client, agent.id, tool_ids)

        # Verify tool is attached
        page = client.agents.tools.list(agent_id=agent.id, limit=100)
        attached = page.items if hasattr(page, "items") else page
        attached_names = [t.name for t in attached]
        assert "execute_shell_command" in attached_names

    @pytest.mark.timeout(60)
    def test_agent_calls_shell_tool(self):
        """Ask agent to run a command — it should use execute_shell_command."""
        from letta_client import Letta

        from jarvis.agent.factory import get_or_create_agent
        from jarvis.agent.response import extract_assistant_text
        from jarvis.settings import load_settings
        from jarvis.tools.registry import register_tools, sync_agent_tools
        from jarvis.tools.shell import execute_shell_command

        settings = load_settings()
        client = Letta(base_url=settings.letta.base_url)

        tool_ids = register_tools(client, [execute_shell_command])
        agent = get_or_create_agent(client, settings)
        sync_agent_tools(client, agent.id, tool_ids)

        response = client.agents.messages.create(
            agent_id=agent.id,
            messages=[
                {"role": "user", "content": "Please run this command: echo hello_from_jarvis"}
            ],
        )

        reply = extract_assistant_text(response)
        assert reply is not None
        all_text = str(response.messages).lower()
        assert "hello_from_jarvis" in reply.lower() or "hello_from_jarvis" in all_text

    @pytest.mark.timeout(60)
    def test_agent_calls_web_search(self):
        """Ask agent to search the web — it should use web_search tool."""
        from letta_client import Letta

        from jarvis.agent.factory import get_or_create_agent
        from jarvis.agent.response import extract_assistant_text
        from jarvis.settings import load_settings
        from jarvis.tools.registry import register_tools, sync_agent_tools
        from jarvis.tools.web_search import web_search

        settings = load_settings()
        client = Letta(base_url=settings.letta.base_url)

        tool_ids = register_tools(client, [web_search])
        agent = get_or_create_agent(client, settings)
        sync_agent_tools(client, agent.id, tool_ids)

        response = client.agents.messages.create(
            agent_id=agent.id,
            messages=[
                {"role": "user", "content": "Search the web for: Python programming language"}
            ],
        )

        # Check that the tool was invoked (tool_call in messages) or results in reply
        all_text = str(response.messages).lower()
        reply = extract_assistant_text(response)
        assert reply is not None
        assert "web_search" in all_text or "python" in reply.lower()
