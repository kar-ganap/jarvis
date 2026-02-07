from __future__ import annotations


def notion_search(query: str, max_results: int = 10) -> str:
    """Search Notion pages and databases by query text.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        Formatted list of matching pages with IDs and titles.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/notion/search",
        json={"query": query, "max_results": max_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No Notion pages found."
    lines = []
    for r in results:
        lines.append(f"  [{r['id']}] {r.get('title', '(untitled)')}")
    return f"Found {len(results)} pages:\n" + "\n".join(lines)


def notion_read_page(page_id: str) -> str:
    """Read a Notion page and return its title and text content.

    Args:
        page_id: The Notion page ID to read.

    Returns:
        Page title and text content.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/notion/read",
        json={"page_id": page_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "(untitled)")
    content = data.get("content", "(empty)")
    return f"Page: {title}\n\n{content}"


def notion_create_page(
    parent_id: str, title: str, content: str = "",
) -> str:
    """Create a new Notion page under a parent page.

    Args:
        parent_id: ID of the parent page.
        title: Title for the new page.
        content: Optional text content for the page body.

    Returns:
        Confirmation with page ID and URL.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/notion/create",
        json={
            "parent_id": parent_id,
            "title": title,
            "content": content,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return (
        f"Created page '{title}' "
        f"(id: {data.get('id', 'unknown')}, "
        f"url: {data.get('url', '')})"
    )


def notion_append_blocks(page_id: str, content: str) -> str:
    """Append text content as blocks to an existing Notion page.

    Args:
        page_id: The Notion page ID to append to.
        content: Text to append. Paragraphs separated by blank lines.

    Returns:
        Confirmation with number of blocks added.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/notion/append",
        json={"page_id": page_id, "content": content},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    count = data.get("block_count", 0)
    return f"Appended {count} blocks to page {page_id}"


def notion_query_database(
    database_id: str, filter_json: str = "",
) -> str:
    """Query a Notion database with an optional JSON filter.

    Args:
        database_id: The Notion database ID to query.
        filter_json: Optional JSON string with filter criteria.

    Returns:
        Formatted list of matching database entries.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/notion/query_db",
        json={"database_id": database_id, "filter_json": filter_json},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No results found."
    lines = []
    for r in results:
        title = r.get("title", r.get("id", ""))
        lines.append(f"  [{r['id']}] {title}")
    return f"Found {len(results)} entries:\n" + "\n".join(lines)


TOOLS = [
    notion_search,
    notion_read_page,
    notion_create_page,
    notion_append_blocks,
    notion_query_database,
]
