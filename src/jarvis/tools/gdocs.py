from __future__ import annotations


def gdocs_list(max_results: int = 10) -> str:
    """List Google Docs documents.

    Args:
        max_results: Maximum number of documents to return.

    Returns:
        Formatted list of documents with IDs and names.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/docs/list",
        json={"max_results": max_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No documents found."
    lines = []
    for r in results:
        name = r.get("name", "(untitled)")
        modified = r.get("modified", "")
        lines.append(f"  [{r['id']}] {name} — modified {modified}")
    return f"Found {len(results)} documents:\n" + "\n".join(lines)


def gdocs_read(document_id: str) -> str:
    """Read text content from a Google Doc.

    Args:
        document_id: The document ID to read.

    Returns:
        Document title and text content.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/docs/read",
        json={"document_id": document_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "(untitled)")
    content = data.get("content", "(empty)")
    return f"Document: {title}\n\n{content}"


def gdocs_create(title: str) -> str:
    """Create a new Google Doc.

    Args:
        title: Title for the new document.

    Returns:
        Confirmation with document ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/docs/create",
        json={"title": title},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Created document '{data.get('title', title)}' (id: {data.get('id', 'unknown')})"


def gdocs_append(document_id: str, text: str) -> str:
    """Append text to the end of a Google Doc.

    Args:
        document_id: The document ID to append to.
        text: Text to append.

    Returns:
        Confirmation that text was appended.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/docs/append",
        json={"document_id": document_id, "text": text},
        timeout=30,
    )
    resp.raise_for_status()
    return f"Appended text to document {document_id}"


TOOLS = [gdocs_list, gdocs_read, gdocs_create, gdocs_append]
