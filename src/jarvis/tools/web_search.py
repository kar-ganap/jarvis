from __future__ import annotations


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information using Tavily.

    Args:
        query: The search query.
        max_results: Number of results to return (1-10). Defaults to 5.

    Returns:
        A formatted string with search results including titles, URLs, and snippets.
    """
    import os

    import requests

    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "ERROR: TAVILY_API_KEY not set."

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": min(max_results, 10),
            "include_answer": True,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    parts = []
    if data.get("answer"):
        parts.append(f"Summary: {data['answer']}\n")
    for i, r in enumerate(data.get("results", []), 1):
        parts.append(
            f"{i}. {r['title']}\n   {r['url']}\n   {r.get('content', '')[:200]}"
        )

    return "\n\n".join(parts) if parts else "No results found."


TOOLS = [web_search]
