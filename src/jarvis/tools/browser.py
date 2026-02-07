from __future__ import annotations


def browser_navigate(url: str) -> str:
    """Navigate to a URL and return the page title and text content.

    Args:
        url: The URL to navigate to.

    Returns:
        Page title and truncated text content.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/browser/navigate",
        json={"url": url},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "")
    text = data.get("text", "")
    return f"Title: {title}\nURL: {url}\n\n{text}"


def browser_screenshot(url: str) -> str:
    """Take a screenshot of a web page.

    Args:
        url: The URL to screenshot.

    Returns:
        Path to the saved PNG screenshot.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/browser/screenshot",
        json={"url": url},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    title = data.get("title", "")
    path = data.get("path", "")
    return f"Screenshot of '{title}' saved to {path}"


def browser_extract(url: str, selector: str) -> str:
    """Extract text from elements matching a CSS selector on a web page.

    Args:
        url: The URL to navigate to.
        selector: CSS selector to match elements.

    Returns:
        Extracted text content from matching elements.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/browser/extract",
        json={"url": url, "selector": selector},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data.get("text", "")
    count = data.get("count", 0)
    return f"Extracted from {count} elements:\n{text}"


TOOLS = [browser_navigate, browser_screenshot, browser_extract]
