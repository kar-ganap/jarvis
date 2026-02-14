"""Mock Letta client for offline evaluation."""
from __future__ import annotations

from unittest.mock import MagicMock


def make_mock_response(
    tool_names: list[str],
    reply_text: str = "Done.",
) -> MagicMock:
    """Build a fake Letta response with tool_call_messages."""
    messages: list[MagicMock] = []
    for name in tool_names:
        tc_msg = MagicMock()
        tc_msg.message_type = "tool_call_message"
        tc_msg.tool_call = MagicMock()
        tc_msg.tool_call.name = name
        tc_msg.tool_call.arguments = "{}"
        tc_msg.tool_call.tool_call_id = f"tc_{name}"
        messages.append(tc_msg)

    if reply_text:
        assist_msg = MagicMock()
        assist_msg.message_type = "assistant_message"
        assist_msg.content = reply_text
        messages.append(assist_msg)

    resp = MagicMock()
    resp.messages = messages
    return resp


class MockLettaClient:
    """Offline Letta client that returns canned tool responses."""

    def __init__(self) -> None:
        self.agents = MagicMock()
        self.agents.messages.create = self._create
        self._pending_response: MagicMock | None = None

    def _create(self, **kwargs: object) -> MagicMock:
        if self._pending_response is None:
            return make_mock_response([])
        return self._pending_response

    def set_response(self, response: MagicMock) -> None:
        self._pending_response = response
