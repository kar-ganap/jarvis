from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestAgentTrigger:
    async def test_send_formats_message(self):
        from jarvis.scheduler.triggers import AgentTrigger

        client = MagicMock()
        trigger = AgentTrigger(client=client, agent_id="agent-123")

        with patch("asyncio.to_thread") as mock_to_thread:
            await trigger.send("Reminder: check the PR")

        mock_to_thread.assert_called_once()
        call_args = mock_to_thread.call_args
        # First arg is the function, then the kwargs
        assert call_args[1]["messages"][0]["content"] == (
            "[scheduler|system] Reminder: check the PR"
        )

    async def test_send_uses_correct_agent(self):
        from jarvis.scheduler.triggers import AgentTrigger

        client = MagicMock()
        trigger = AgentTrigger(client=client, agent_id="agent-456")

        with patch("asyncio.to_thread") as mock_to_thread:
            await trigger.send("test")

        call_args = mock_to_thread.call_args
        assert call_args[1]["agent_id"] == "agent-456"
