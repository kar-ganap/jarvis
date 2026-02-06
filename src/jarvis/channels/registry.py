from __future__ import annotations

import structlog

from jarvis.channels.base import Channel, ChannelType
from jarvis.channels.cli import CLIChannel
from jarvis.channels.slack import SlackChannel
from jarvis.settings import JarvisSettings

log = structlog.get_logger()


class ChannelRegistry:
    """Builds enabled channels from settings."""

    @staticmethod
    def build(settings: JarvisSettings) -> dict[ChannelType, Channel]:
        channels: dict[ChannelType, Channel] = {}

        # CLI is always enabled
        channels[ChannelType.CLI] = CLIChannel(
            user_name=settings.user.name,
        )

        # Slack — enabled if configured
        if settings.slack.enabled:
            channels[ChannelType.SLACK] = SlackChannel(
                bot_token=settings.slack.bot_token,
                app_token=settings.slack.app_token,
            )
            log.info("registry.slack_enabled")

        log.info(
            "registry.channels_built",
            channels=[ct.value for ct in channels],
        )
        return channels
