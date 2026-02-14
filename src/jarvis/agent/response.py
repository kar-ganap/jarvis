from __future__ import annotations

import json
from typing import Any


def extract_assistant_text(response: Any) -> str | None:  # noqa: ANN401
    """Extract the assistant's text from a Letta message response.

    Returns the concatenated text of all assistant_message items,
    or None if no assistant message was found.
    """
    texts = []
    for msg in response.messages:
        if msg.message_type == "assistant_message" and msg.content:
            texts.append(msg.content)
    return "\n".join(texts) if texts else None


def extract_tool_calls(response: Any) -> list[dict[str, Any]]:  # noqa: ANN401
    """Extract tool call names and arguments from a Letta message response.

    Returns a list of dicts with 'tool_name' and 'arguments' keys.
    """
    calls: list[dict[str, Any]] = []
    for msg in response.messages:
        if msg.message_type == "tool_call_message" and hasattr(msg, "tool_call"):
            tc = msg.tool_call
            try:
                args = json.loads(tc.arguments) if tc.arguments else {}
            except (json.JSONDecodeError, TypeError):
                args = tc.arguments
            calls.append({"tool_name": tc.name, "arguments": args})
    return calls
