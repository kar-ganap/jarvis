import uuid

import pytest


@pytest.fixture()
def test_agent_name() -> str:
    """Generate a unique agent name for test isolation."""
    return f"test-jarvis-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def cleanup_agent(letta_client, test_agent_name):
    """Delete the test agent after the test completes."""
    yield
    # Teardown: find and delete the test agent
    page = letta_client.agents.list(name=test_agent_name)
    for agent in page.items:
        letta_client.agents.delete(agent_id=agent.id)


class TestAgentCreation:
    def test_create_agent(
        self, letta_client, integration_settings, test_agent_name, cleanup_agent
    ) -> None:
        """Create an agent and verify it has persona + human blocks."""
        from jarvis.agent.factory import get_or_create_agent

        integration_settings.agent.name = test_agent_name
        agent = get_or_create_agent(letta_client, integration_settings)

        assert agent.id is not None
        assert agent.name == test_agent_name

        # Verify memory blocks exist
        blocks = letta_client.agents.blocks.list(agent_id=agent.id)
        block_labels = {b.label for b in blocks}
        assert "persona" in block_labels
        assert "human" in block_labels

    def test_agent_responds(
        self, letta_client, integration_settings, test_agent_name, cleanup_agent
    ) -> None:
        """Send a message to the agent and get a non-empty response."""
        from jarvis.agent.factory import get_or_create_agent

        integration_settings.agent.name = test_agent_name
        agent = get_or_create_agent(letta_client, integration_settings)

        response = letta_client.agents.messages.create(
            agent_id=agent.id,
            messages=[{"role": "user", "content": "Hello, introduce yourself briefly."}],
        )

        assistant_messages = [
            m for m in response.messages if m.message_type == "assistant_message"
        ]
        assert len(assistant_messages) > 0
        assert len(assistant_messages[0].content) > 0

    def test_agent_idempotent(
        self, letta_client, integration_settings, test_agent_name, cleanup_agent
    ) -> None:
        """Creating the same agent twice returns the same agent."""
        from jarvis.agent.factory import get_or_create_agent

        integration_settings.agent.name = test_agent_name
        agent1 = get_or_create_agent(letta_client, integration_settings)
        agent2 = get_or_create_agent(letta_client, integration_settings)

        assert agent1.id == agent2.id
