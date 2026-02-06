from __future__ import annotations

import asyncio

import structlog
from letta_client import Letta

from jarvis.agent.factory import get_or_create_agent
from jarvis.channels.registry import ChannelRegistry
from jarvis.channels.router import MessageRouter
from jarvis.settings import JarvisSettings

log = structlog.get_logger()


class JarvisApp:
    """Application orchestrator — wires agent, channels, and router."""

    def __init__(self, settings: JarvisSettings) -> None:
        self.settings = settings

    async def start(self) -> None:
        """Bootstrap and run the application."""
        log.info("app.starting")

        client = Letta(base_url=self.settings.letta.base_url)
        agent = get_or_create_agent(client, self.settings)
        log.info("app.agent_ready", agent_id=agent.id)

        channels = ChannelRegistry.build(self.settings)

        router = MessageRouter(
            client=client,
            agent_id=agent.id,
            channels=channels,
        )

        # Start all channels concurrently
        tasks = [
            asyncio.create_task(ch.start(on_message=router.handle_inbound))
            for ch in channels.values()
        ]
        await asyncio.gather(*tasks)

    async def stop(self) -> None:
        """Graceful shutdown."""
        log.info("app.stopping")
