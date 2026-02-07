from __future__ import annotations


def gslides_list(max_results: int = 10) -> str:
    """List Google Slides presentations.

    Args:
        max_results: Maximum number of presentations to return.

    Returns:
        Formatted list of presentations with IDs and names.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/slides/list",
        json={"max_results": max_results},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No presentations found."
    lines = []
    for r in results:
        name = r.get("name", "(untitled)")
        modified = r.get("modified", "")
        lines.append(f"  [{r['id']}] {name} — modified {modified}")
    return f"Found {len(results)} presentations:\n" + "\n".join(lines)


def gslides_read(presentation_id: str) -> str:
    """Read all text from a Google Slides presentation.

    Args:
        presentation_id: The presentation ID to read.

    Returns:
        Presentation title and text content from all slides.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/slides/read",
        json={"presentation_id": presentation_id},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "(untitled)")
    slides = data.get("slides", [])
    if not slides:
        return f"Presentation: {title}\n(no slides)"
    lines = [f"Presentation: {title}\n"]
    for s in slides:
        text = s.get("text", "").strip()
        if text:
            lines.append(f"--- Slide {s['slide_number']} ---\n{text}")
    return "\n".join(lines)


def gslides_create(title: str) -> str:
    """Create a new Google Slides presentation.

    Args:
        title: Title for the new presentation.

    Returns:
        Confirmation with presentation ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/slides/create",
        json={"title": title},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Created presentation '{data.get('title', title)}' (id: {data.get('id', 'unknown')})"


def gslides_add_slide(presentation_id: str, title: str, body: str) -> str:
    """Add a slide with title and body text to a presentation.

    Args:
        presentation_id: The presentation to add a slide to.
        title: Title text for the slide.
        body: Body text for the slide.

    Returns:
        Confirmation with slide ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/slides/add_slide",
        json={"presentation_id": presentation_id, "title": title, "body": body},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Added slide (id: {data.get('slide_id', 'unknown')}) to presentation {presentation_id}"


TOOLS = [gslides_list, gslides_read, gslides_create, gslides_add_slide]
