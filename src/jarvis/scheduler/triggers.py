from __future__ import annotations

import asyncio

import structlog

log = structlog.get_logger()


class AgentTrigger:
    """Sends notifications when a scheduled job fires.

    Two things happen on trigger:
    1. Direct notification to the user via router (if routing info provided)
    2. Inform the Letta agent via [scheduler|system] message (for memory)
    """

    def __init__(self, client, agent_id: str, router=None) -> None:
        self._client = client
        self._agent_id = agent_id
        self._router = router

    async def send(
        self,
        context: str,
        notify_channel: str = "",
        notify_recipient: str = "",
    ) -> None:
        """Fire the trigger: notify user directly and inform the agent."""
        # Direct notification to user (reliable path)
        if self._router and notify_channel and notify_recipient:
            from jarvis.channels.base import ChannelType

            log.info(
                "trigger.notify_direct",
                channel=notify_channel,
                recipient=notify_recipient,
            )
            await self._router.send_proactive(
                ChannelType(notify_channel), notify_recipient, context
            )

        # Inform the agent for memory/context
        prefixed = f"[scheduler|system] {context}"
        await asyncio.to_thread(
            self._client.agents.messages.create,
            agent_id=self._agent_id,
            messages=[{"role": "user", "content": prefixed}],
        )
