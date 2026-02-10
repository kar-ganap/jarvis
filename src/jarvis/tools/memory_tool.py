from __future__ import annotations


def save_note(content: str, category: str = "") -> str:
    """Save a note to long-term memory with an optional category tag.

    Args:
        content: The note text to save.
        category: Optional category for organizing notes (e.g. 'preference', 'fact', 'todo').

    Returns:
        Confirmation that the note was saved.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/memory/save",
        json={"content": content, "category": category},
        timeout=30,
    )
    resp.raise_for_status()
    return f"Saved note: {content}"


def recall_notes(query: str, category: str = "", max_results: int = 5) -> str:
    """Search long-term memory for saved notes.

    Args:
        query: Search query to find relevant notes.
        category: Optional category to narrow the search.
        max_results: Maximum number of notes to return.

    Returns:
        Matching notes with timestamps.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/memory/recall",
        json={"query": query, "category": category, "max_results": max_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No matching notes found."
    lines = []
    for r in results:
        lines.append(f"  [{r.get('created_at', '')}] {r['text']}")
    return f"Found {len(results)} notes:\n" + "\n".join(lines)


TOOLS = [save_note, recall_notes]
