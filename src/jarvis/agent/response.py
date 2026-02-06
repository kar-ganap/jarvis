from __future__ import annotations


def extract_assistant_text(response) -> str | None:
    """Extract the assistant's text from a Letta message response.

    Returns the concatenated text of all assistant_message items,
    or None if no assistant message was found.
    """
    texts = []
    for msg in response.messages:
        if msg.message_type == "assistant_message" and msg.content:
            texts.append(msg.content)
    return "\n".join(texts) if texts else None
