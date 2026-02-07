from __future__ import annotations

import json
import os

from notion_client import Client


def _notion_client() -> Client:
    """Build a Notion client from the NOTION_API_KEY env var."""
    token = os.environ.get("NOTION_API_KEY", "")
    if not token:
        raise ValueError(
            "NOTION_API_KEY environment variable not set. "
            "Create an integration at https://www.notion.so/my-integrations"
        )
    return Client(auth=token)


def _extract_title(obj: dict) -> str:
    """Extract the title string from a Notion page or database object."""
    props = obj.get("properties", {})
    for prop in props.values():
        if prop.get("type") == "title":
            title_items = prop.get("title", [])
            if title_items:
                return "".join(
                    item.get("plain_text", "") for item in title_items
                )
    return "(untitled)"


def _extract_block_text(block: dict) -> str:
    """Extract plain text from a single Notion block."""
    block_type = block.get("type", "")
    type_data = block.get(block_type, {})
    rich_text = type_data.get("rich_text", [])
    text = "".join(item.get("plain_text", "") for item in rich_text)
    return text


def notion_search(query: str, max_results: int = 10) -> list[dict]:
    """Search Notion pages and databases by query text."""
    client = _notion_client()
    response = client.search(query=query, page_size=max_results)
    results = []
    for item in response.get("results", []):
        results.append({
            "id": item["id"],
            "type": item.get("object", ""),
            "title": _extract_title(item),
            "url": item.get("url", ""),
        })
    return results


def notion_read_page(page_id: str) -> dict:
    """Read a Notion page: title and all text blocks."""
    client = _notion_client()
    page = client.pages.retrieve(page_id)
    blocks_resp = client.blocks.children.list(page_id)

    text_parts = []
    for block in blocks_resp.get("results", []):
        text = _extract_block_text(block)
        if text:
            text_parts.append(text)

    return {
        "id": page_id,
        "title": _extract_title(page),
        "content": "\n".join(text_parts),
    }


def notion_create_page(
    parent_id: str, title: str, content: str = "",
) -> dict:
    """Create a new page under a parent page."""
    client = _notion_client()

    children = []
    if content:
        for paragraph in content.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                children.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": paragraph}}
                        ]
                    },
                })

    result = client.pages.create(
        parent={"page_id": parent_id},
        properties={
            "title": [{"type": "text", "text": {"content": title}}]
        },
        children=children,
    )

    return {
        "id": result["id"],
        "url": result.get("url", ""),
    }


def notion_append_blocks(page_id: str, content: str) -> dict:
    """Append paragraph blocks to an existing page."""
    client = _notion_client()

    children = []
    for paragraph in content.split("\n\n"):
        paragraph = paragraph.strip()
        if paragraph:
            children.append({
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": paragraph}}
                    ]
                },
            })

    result = client.blocks.children.append(
        block_id=page_id, children=children,
    )

    return {"block_count": len(result.get("results", []))}


def notion_query_database(
    database_id: str, filter_json: str = "",
) -> list[dict]:
    """Query a Notion database with an optional JSON filter."""
    client = _notion_client()

    kwargs: dict = {"database_id": database_id}
    if filter_json:
        kwargs["filter"] = json.loads(filter_json)

    response = client.databases.query(**kwargs)

    results = []
    for item in response.get("results", []):
        entry: dict = {"id": item["id"]}
        props = item.get("properties", {})
        for name, prop in props.items():
            if prop.get("type") == "title":
                title_items = prop.get("title", [])
                entry["title"] = "".join(
                    t.get("plain_text", "") for t in title_items
                )
            elif prop.get("type") == "select":
                sel = prop.get("select")
                entry[name] = sel["name"] if sel else ""
        results.append(entry)

    return results
