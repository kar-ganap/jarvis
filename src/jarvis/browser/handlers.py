from __future__ import annotations

import tempfile
import uuid

from playwright.sync_api import sync_playwright

_pw = None
_browser = None
_context = None

_MAX_TEXT_LENGTH = 10000


def _ensure_browser():
    """Lazy-init Chromium on first use, return persistent context."""
    global _pw, _browser, _context
    if _context is not None:
        return _context
    _pw = sync_playwright().start()
    _browser = _pw.chromium.launch(headless=True)
    _context = _browser.new_context()
    return _context


def browser_navigate(url: str) -> dict:
    """Navigate to URL and return page title and text content."""
    context = _ensure_browser()
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded")
        title = page.title()
        text = page.inner_text("body")
        if len(text) > _MAX_TEXT_LENGTH:
            text = text[:_MAX_TEXT_LENGTH]
        return {"title": title, "url": url, "text": text}
    finally:
        page.close()


def browser_screenshot(url: str) -> dict:
    """Take a screenshot of the URL and return the file path."""
    context = _ensure_browser()
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded")
        title = page.title()
        path = f"{tempfile.gettempdir()}/jarvis_screenshot_{uuid.uuid4().hex[:8]}.png"
        page.screenshot(path=path)
        return {"title": title, "path": path}
    finally:
        page.close()


def browser_extract(url: str, selector: str) -> dict:
    """Extract text from elements matching a CSS selector."""
    context = _ensure_browser()
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded")
        elements = page.query_selector_all(selector)
        texts = [el.inner_text() for el in elements]
        combined = "\n".join(texts)
        if len(combined) > _MAX_TEXT_LENGTH:
            combined = combined[:_MAX_TEXT_LENGTH]
        return {"text": combined, "count": len(elements)}
    finally:
        page.close()


def close_browser() -> None:
    """Shutdown hook — close browser and playwright."""
    global _pw, _browser, _context
    if _browser:
        _browser.close()
    if _pw:
        _pw.stop()
    _pw = None
    _browser = None
    _context = None
