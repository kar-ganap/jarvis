from __future__ import annotations

import structlog

from jarvis.channels.base import Channel, ChannelType
from jarvis.channels.cli import CLIChannel
from jarvis.channels.slack import SlackChannel
from jarvis.channels.whatsapp import WhatsAppChannel
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
            voice_enabled=settings.voice.enabled,
        )

        # Slack — enabled if configured
        if settings.slack.enabled:
            channels[ChannelType.SLACK] = SlackChannel(
                bot_token=settings.slack.bot_token,
                app_token=settings.slack.app_token,
            )
            log.info("registry.slack_enabled")

        # WhatsApp — enabled if configured
        if settings.whatsapp.enabled:
            channels[ChannelType.WHATSAPP] = WhatsAppChannel(
                bridge_url=settings.whatsapp.bridge_url,
                allow_groups=settings.whatsapp.allow_groups,
                allowed_senders=settings.whatsapp.allowed_senders,
            )
            log.info("registry.whatsapp_enabled")

        log.info(
            "registry.channels_built",
            channels=[ct.value for ct in channels],
        )
        return channels
