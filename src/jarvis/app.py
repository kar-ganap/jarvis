from __future__ import annotations

import structlog
from letta_client import Letta

from jarvis.agent.factory import get_or_create_agent
from jarvis.channels.base import ChannelType
from jarvis.channels.cli import CLIChannel
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

        cli = CLIChannel(user_name=self.settings.user.name)
        channels = {ChannelType.CLI: cli}

        router = MessageRouter(
            client=client,
            agent_id=agent.id,
            channels=channels,
        )

        await cli.start(on_message=router.handle_inbound)

    async def stop(self) -> None:
        """Graceful shutdown."""
        log.info("app.stopping")
