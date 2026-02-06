import dataclasses

import pytest


class TestChannelMessage:
    def test_is_frozen(self) -> None:
        from jarvis.channels.base import ChannelMessage, ChannelType, ChannelUser

        user = ChannelUser(id="u1", display_name="Alice")
        msg = ChannelMessage(channel_type=ChannelType.CLI, user=user, text="hello")

        with pytest.raises(dataclasses.FrozenInstanceError):
            msg.text = "modified"  # type: ignore[misc]


class TestOutboundMessage:
    def test_is_frozen(self) -> None:
        from jarvis.channels.base import ChannelType, OutboundMessage

        msg = OutboundMessage(channel_type=ChannelType.CLI, recipient_id="u1", text="hi")

        with pytest.raises(dataclasses.FrozenInstanceError):
            msg.text = "modified"  # type: ignore[misc]


class TestChannelType:
    def test_values(self) -> None:
        from jarvis.channels.base import ChannelType

        assert ChannelType.CLI == "cli"
        assert ChannelType.SLACK == "slack"
        assert ChannelType.WHATSAPP == "whatsapp"
        assert ChannelType.GOOGLE_CHAT == "google_chat"
