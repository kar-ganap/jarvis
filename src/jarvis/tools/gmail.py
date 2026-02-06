from __future__ import annotations


def gmail_search(query: str, max_results: int = 5) -> str:
    """Search Gmail for messages matching a query.

    Args:
        query: Gmail search query (e.g. 'from:alice subject:meeting').
        max_results: Maximum number of results to return.

    Returns:
        Formatted list of matching emails with IDs, subjects, and senders.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gmail/search",
        json={"query": query, "max_results": max_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No emails found."
    lines = []
    for r in results:
        lines.append(f"  [{r['id']}] {r.get('subject', '(no subject)')} — {r.get('from', '')}")
    return f"Found {len(results)} emails:\n" + "\n".join(lines)


def gmail_read(message_id: str) -> str:
    """Read a single email by its message ID.

    Args:
        message_id: The Gmail message ID to read.

    Returns:
        The email with subject, sender, date, and body text.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gmail/read",
        json={"message_id": message_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return (
        f"Subject: {data.get('subject', '(none)')}\n"
        f"From: {data.get('from', '(unknown)')}\n"
        f"To: {data.get('to', '')}\n"
        f"Date: {data.get('date', '')}\n"
        f"\n{data.get('body', '(no body)')}"
    )


def gmail_send(to: str, subject: str, body: str) -> str:
    """Send an email.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.

    Returns:
        Confirmation with message ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gmail/send",
        json={"to": to, "subject": subject, "body": body},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Email sent to {to} (id: {data.get('id', 'unknown')})"


def gmail_draft(to: str, subject: str, body: str) -> str:
    """Create an email draft.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain text email body.

    Returns:
        Confirmation with draft ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gmail/draft",
        json={"to": to, "subject": subject, "body": body},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Draft created (id: {data.get('id', 'unknown')})"


TOOLS = [gmail_search, gmail_read, gmail_send, gmail_draft]
