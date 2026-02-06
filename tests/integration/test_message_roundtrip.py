import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest


@pytest.fixture()
def roundtrip_agent_name() -> str:
    return f"test-roundtrip-{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def cleanup_roundtrip_agent(letta_client, roundtrip_agent_name):
    yield
    page = letta_client.agents.list(name=roundtrip_agent_name)
    for agent in page.items:
        letta_client.agents.delete(agent_id=agent.id)


class TestMessageRoundtrip:
    def test_router_roundtrip(
        self,
        letta_client,
        integration_settings,
        roundtrip_agent_name,
        cleanup_roundtrip_agent,
    ) -> None:
        """Send a message through the router with a mock channel, verify reply arrives."""
        from jarvis.agent.factory import get_or_create_agent
        from jarvis.channels.base import (
            ChannelMessage,
            ChannelType,
            ChannelUser,
        )
        from jarvis.channels.router import MessageRouter

        integration_settings.agent.name = roundtrip_agent_name
        agent = get_or_create_agent(letta_client, integration_settings)

        # Use a mock channel to capture the outbound reply
        mock_channel = AsyncMock()
        mock_channel.channel_type = ChannelType.CLI

        router = MessageRouter(
            client=letta_client,
            agent_id=agent.id,
            channels={ChannelType.CLI: mock_channel},
        )

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(id="test-user", display_name="Tester"),
            text="Hello, what is your name?",
        )

        asyncio.run(router.handle_inbound(msg))

        # The mock channel should have received an outbound reply
        mock_channel.send.assert_called_once()
        outbound = mock_channel.send.call_args[0][0]
        assert len(outbound.text) > 0
        assert outbound.recipient_id == "test-user"
