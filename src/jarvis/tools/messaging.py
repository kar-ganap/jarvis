from __future__ import annotations


def send_message_to_user(channel: str, recipient_id: str, text: str) -> str:
    """Send a message to the user on a specific channel.

    Args:
        channel: The channel to send on ('cli' or 'slack').
        recipient_id: The recipient identifier (channel ID for Slack).
        text: The message text to send.

    Returns:
        Confirmation or error message.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    url = f"http://{host}:{port}/outbound"

    resp = requests.post(
        url,
        json={
            "channel": channel,
            "recipient_id": recipient_id,
            "text": text,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return f"OK: Message sent to {channel}"


TOOLS = [send_message_to_user]
