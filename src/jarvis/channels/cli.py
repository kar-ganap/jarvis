from __future__ import annotations

import asyncio

import structlog

from jarvis.channels.base import (
    Channel,
    ChannelMessage,
    ChannelType,
    ChannelUser,
    InboundHandler,
    OutboundMessage,
)

log = structlog.get_logger()


class CLIChannel(Channel):
    """Dev/testing channel using stdin/stdout."""

    def __init__(self, user_name: str = "User") -> None:
        self._user_name = user_name
        self._running = False

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.CLI

    async def start(self, on_message: InboundHandler) -> None:
        """Read lines from stdin, dispatch as messages."""
        self._running = True
        user = ChannelUser(id="cli-user", display_name=self._user_name)

        log.info("cli.started")
        while self._running:
            try:
                line = await asyncio.to_thread(input, "You: ")
            except EOFError:
                break

            stripped = line.strip()
            if not stripped:
                continue
            if stripped.lower() in ("quit", "exit"):
                break

            msg = ChannelMessage(
                channel_type=ChannelType.CLI, user=user, text=stripped
            )
            await on_message(msg)

        self._running = False
        log.info("cli.stopped")

    async def stop(self) -> None:
        self._running = False

    async def send(self, message: OutboundMessage) -> None:
        print(f"Jarvis: {message.text}")
