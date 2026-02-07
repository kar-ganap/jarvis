from __future__ import annotations

import asyncio
import os

import structlog
from letta_client import Letta

from jarvis.agent.factory import get_or_create_agent
from jarvis.channels.base import ChannelType
from jarvis.channels.registry import ChannelRegistry
from jarvis.channels.router import MessageRouter
from jarvis.http_server import InternalServer
from jarvis.monitoring.health import mark_started
from jarvis.scheduler.engine import SchedulerEngine
from jarvis.scheduler.triggers import AgentTrigger
from jarvis.settings import JarvisSettings

log = structlog.get_logger()


class JarvisApp:
    """Application orchestrator — wires agent, channels, and router."""

    def __init__(self, settings: JarvisSettings) -> None:
        self.settings = settings

    async def start(self) -> None:
        """Bootstrap and run the application."""
        log.info("app.starting")

        # Set Google token path for handlers
        os.environ.setdefault("GOOGLE_TOKEN_PATH", self.settings.google.token_path)

        client = Letta(base_url=self.settings.letta.base_url)
        agent, tool_count = get_or_create_agent(client, self.settings)
        log.info("app.agent_ready", agent_id=agent.id, tool_count=tool_count)

        mark_started()

        channels = ChannelRegistry.build(self.settings)

        router = MessageRouter(
            client=client,
            agent_id=agent.id,
            channels=channels,
        )

        # Scheduler + trigger
        scheduler = SchedulerEngine()
        scheduler.start()
        trigger = AgentTrigger(client=client, agent_id=agent.id, router=router)

        # Internal HTTP server
        whatsapp_channel = channels.get(ChannelType.WHATSAPP)
        channel_names = [ct.value for ct in channels]
        http_server = InternalServer(
            router=router,
            scheduler=scheduler,
            trigger=trigger,
            whatsapp_channel=whatsapp_channel,
            port=self.settings.http.port,
            letta_client=client,
            agent_id=agent.id,
            channel_names=channel_names,
            tool_count=tool_count,
            metrics_enabled=self.settings.monitoring.metrics_enabled,
        )

        # Start HTTP server + all channels concurrently
        tasks = [
            asyncio.create_task(http_server.start()),
            *[
                asyncio.create_task(ch.start(on_message=router.handle_inbound))
                for ch in channels.values()
            ],
        ]
        await asyncio.gather(*tasks)

    async def stop(self) -> None:
        """Graceful shutdown."""
        log.info("app.stopping")
