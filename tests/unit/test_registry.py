from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock


class TestCollectTools:
    def test_collects_from_multiple_modules(self):
        from jarvis.tools.registry import collect_tools

        func_a = lambda: None  # noqa: E731
        func_b = lambda: None  # noqa: E731
        mod1 = SimpleNamespace(TOOLS=[func_a])
        mod2 = SimpleNamespace(TOOLS=[func_b])

        result = collect_tools(mod1, mod2)
        assert result == [func_a, func_b]

    def test_skips_module_without_tools(self):
        from jarvis.tools.registry import collect_tools

        func_a = lambda: None  # noqa: E731
        mod1 = SimpleNamespace(TOOLS=[func_a])
        mod2 = SimpleNamespace()  # no TOOLS attribute

        result = collect_tools(mod1, mod2)
        assert result == [func_a]


class TestRegisterTools:
    def test_calls_upsert_for_each_function(self):
        from jarvis.tools.registry import register_tools

        client = MagicMock()
        func_a = lambda: None  # noqa: E731
        func_b = lambda: None  # noqa: E731

        mock_tool_a = MagicMock(id="tool-a", name="func_a")
        mock_tool_b = MagicMock(id="tool-b", name="func_b")
        client.tools.upsert_from_function.side_effect = [mock_tool_a, mock_tool_b]

        ids = register_tools(client, [func_a, func_b])

        assert ids == ["tool-a", "tool-b"]
        assert client.tools.upsert_from_function.call_count == 2
        client.tools.upsert_from_function.assert_any_call(func=func_a)
        client.tools.upsert_from_function.assert_any_call(func=func_b)


class TestSyncAgentTools:
    def test_attaches_missing_tools(self):
        from jarvis.tools.registry import sync_agent_tools

        client = MagicMock()
        # Agent already has tool-a, but not tool-b
        existing_tool = MagicMock(id="tool-a")
        client.agents.tools.list.return_value = [existing_tool]

        sync_agent_tools(client, "agent-123", ["tool-a", "tool-b"])

        client.agents.tools.attach.assert_called_once_with(
            agent_id="agent-123", tool_id="tool-b"
        )

    def test_skips_already_attached(self):
        from jarvis.tools.registry import sync_agent_tools

        client = MagicMock()
        existing_tool = MagicMock(id="tool-a")
        client.agents.tools.list.return_value = [existing_tool]

        sync_agent_tools(client, "agent-123", ["tool-a"])

        client.agents.tools.attach.assert_not_called()
