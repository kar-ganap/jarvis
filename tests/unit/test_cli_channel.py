class TestCLIChannel:
    def test_channel_type(self) -> None:
        from jarvis.channels.base import ChannelType
        from jarvis.channels.cli import CLIChannel

        channel = CLIChannel(user_name="Kartik")
        assert channel.channel_type == ChannelType.CLI

    def test_send_prints_output(self, capsys) -> None:
        import asyncio

        from jarvis.channels.base import ChannelType, OutboundMessage
        from jarvis.channels.cli import CLIChannel

        channel = CLIChannel(user_name="Kartik")
        outbound = OutboundMessage(
            channel_type=ChannelType.CLI, recipient_id="u1", text="Hello there!"
        )
        asyncio.run(channel.send(outbound))

        captured = capsys.readouterr()
        assert "Jarvis: Hello there!" in captured.out
