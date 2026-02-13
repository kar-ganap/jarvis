from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum


class ChannelType(StrEnum):
    CLI = "cli"
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    GOOGLE_CHAT = "google_chat"


@dataclass(frozen=True)
class ChannelUser:
    id: str
    display_name: str


@dataclass(frozen=True)
class ChannelMessage:
    """Normalized inbound message from any channel."""

    channel_type: ChannelType
    user: ChannelUser
    text: str
    raw: dict | None = None
    audio_data: bytes | None = None
    audio_mime: str | None = None


@dataclass(frozen=True)
class OutboundMessage:
    """Message to send back to a channel."""

    channel_type: ChannelType
    recipient_id: str
    text: str
    audio_data: bytes | None = None
    audio_mime: str | None = None


InboundHandler = Callable[[ChannelMessage], Awaitable[None]]


class Channel(ABC):
    """Abstract base for all messaging channels."""

    @property
    @abstractmethod
    def channel_type(self) -> ChannelType: ...

    @abstractmethod
    async def start(self, on_message: InboundHandler) -> None:
        """Start listening. Call on_message for each inbound message."""

    @abstractmethod
    async def stop(self) -> None:
        """Graceful shutdown."""

    @abstractmethod
    async def send(self, message: OutboundMessage) -> None:
        """Send an outbound message."""
