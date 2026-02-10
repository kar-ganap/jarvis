import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_letta_response(assistant_text: str | None) -> MagicMock:
    """Create a mock Letta response with an optional assistant message."""
    response = MagicMock()
    if assistant_text:
        msg = MagicMock()
        msg.message_type = "assistant_message"
        msg.content = assistant_text
        response.messages = [msg]
    else:
        msg = MagicMock()
        msg.message_type = "tool_call_message"
        msg.content = ""
        response.messages = [msg]
    return response


@pytest.fixture()
def mock_channel() -> AsyncMock:
    from jarvis.channels.base import ChannelType

    channel = AsyncMock()
    channel.channel_type = ChannelType.CLI
    channel.send = AsyncMock()
    return channel


@pytest.fixture()
def router(mock_letta_client: MagicMock, mock_channel: AsyncMock):
    from jarvis.channels.base import ChannelType
    from jarvis.channels.router import MessageRouter

    return MessageRouter(
        client=mock_letta_client,
        agent_id="agent-test-12345",
        channels={ChannelType.CLI: mock_channel},
    )


class TestHandleInbound:
    def test_sends_to_letta_with_prefix(
        self, router, mock_letta_client: MagicMock
    ) -> None:
        from jarvis.channels.base import ChannelMessage, ChannelType, ChannelUser

        mock_letta_client.agents.messages.create.return_value = _make_letta_response(
            "Hi!"
        )

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(id="u1", display_name="Kartik"),
            text="hello",
        )
        asyncio.run(router.handle_inbound(msg))

        call_kwargs = mock_letta_client.agents.messages.create.call_args.kwargs
        assert call_kwargs["agent_id"] == "agent-test-12345"
        sent_content = call_kwargs["messages"][0]["content"]
        assert sent_content == "[cli|u1|Kartik] hello"

    def test_sends_reply_to_channel(
        self, router, mock_letta_client: MagicMock, mock_channel: AsyncMock
    ) -> None:
        from jarvis.channels.base import ChannelMessage, ChannelType, ChannelUser

        mock_letta_client.agents.messages.create.return_value = _make_letta_response(
            "Hello back!"
        )

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(id="u1", display_name="Kartik"),
            text="hi",
        )
        asyncio.run(router.handle_inbound(msg))

        mock_channel.send.assert_called_once()
        outbound = mock_channel.send.call_args[0][0]
        assert outbound.text == "Hello back!"
        assert outbound.recipient_id == "u1"

    def test_no_reply_when_no_assistant_text(
        self, router, mock_letta_client: MagicMock, mock_channel: AsyncMock
    ) -> None:
        from jarvis.channels.base import ChannelMessage, ChannelType, ChannelUser

        mock_letta_client.agents.messages.create.return_value = _make_letta_response(
            None
        )

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(id="u1", display_name="Kartik"),
            text="do something silently",
        )
        asyncio.run(router.handle_inbound(msg))

        mock_channel.send.assert_not_called()


class TestSendProactive:
    def test_sends_to_correct_channel(
        self, router, mock_channel: AsyncMock
    ) -> None:
        from jarvis.channels.base import ChannelType

        asyncio.run(
            router.send_proactive(ChannelType.CLI, "u1", "Reminder: check PR")
        )

        mock_channel.send.assert_called_once()
        outbound = mock_channel.send.call_args[0][0]
        assert outbound.text == "Reminder: check PR"
        assert outbound.channel_type == ChannelType.CLI


class TestMessageCounters:
    def test_inbound_increments_message_counter(
        self, router, mock_letta_client: MagicMock, mock_channel: AsyncMock
    ) -> None:
        """handle_inbound increments MESSAGE_COUNT for inbound direction."""
        from jarvis.channels.base import ChannelMessage, ChannelType, ChannelUser
        from jarvis.monitoring.metrics import MESSAGE_COUNT

        mock_letta_client.agents.messages.create.return_value = _make_letta_response(
            "reply"
        )

        before = MESSAGE_COUNT.labels(
            channel="cli", direction="inbound"
        )._value.get()

        msg = ChannelMessage(
            channel_type=ChannelType.CLI,
            user=ChannelUser(id="u1", display_name="Kartik"),
            text="test",
        )
        asyncio.run(router.handle_inbound(msg))

        after = MESSAGE_COUNT.labels(
            channel="cli", direction="inbound"
        )._value.get()
        assert after >= before + 1

    def test_outbound_increments_message_counter(
        self, router, mock_letta_client: MagicMock, mock_channel: AsyncMock
    ) -> None:
        """send_proactive increments MESSAGE_COUNT for outbound direction."""
        from jarvis.channels.base import ChannelType
        from jarvis.monitoring.metrics import MESSAGE_COUNT

        before = MESSAGE_COUNT.labels(
            channel="cli", direction="outbound"
        )._value.get()

        asyncio.run(
            router.send_proactive(ChannelType.CLI, "u1", "Hello")
        )

        after = MESSAGE_COUNT.labels(
            channel="cli", direction="outbound"
        )._value.get()
        assert after >= before + 1
