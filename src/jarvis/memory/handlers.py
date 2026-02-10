from __future__ import annotations


def memory_save(
    letta_client, agent_id: str, content: str, category: str = "",
) -> dict:
    """Insert a note into archival memory with optional category tag."""
    tags = [category] if category else []
    letta_client.agents.passages.create(
        agent_id=agent_id, text=content, tags=tags,
    )
    return {"status": "saved"}


def memory_recall(
    letta_client, agent_id: str, query: str,
    category: str = "", max_results: int = 5,
) -> list[dict]:
    """Search archival memory, optionally filter by category."""
    search_query = f"[{category}] {query}" if category else query
    response = letta_client.agents.passages.search(
        agent_id=agent_id, query=search_query, top_k=max_results,
    )
    # Handle both PassageSearchResponse (real) and plain list (mock)
    entries = response.results if hasattr(response, "results") else response
    return [
        {
            "text": e.content if hasattr(e, "content") else e.text,
            "created_at": str(
                e.timestamp if hasattr(e, "timestamp") else e.created_at
            ),
        }
        for e in entries
    ]
