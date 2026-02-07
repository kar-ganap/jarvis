from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_playwright():
    """Create a mock Playwright chain: pw.chromium.launch().new_context().new_page()."""
    mock_page = MagicMock()
    mock_page.title.return_value = "Example Page"
    mock_page.inner_text.return_value = "Hello world content"
    mock_page.close = MagicMock()

    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page

    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_pw = MagicMock()
    mock_pw.chromium.launch.return_value = mock_browser

    # sync_playwright() returns a context manager; .start() returns the pw instance
    mock_cm = MagicMock()
    mock_cm.start.return_value = mock_pw
    mock_sync = MagicMock(return_value=mock_cm)

    return mock_sync, mock_pw, mock_browser, mock_context, mock_page


class TestBrowserNavigate:
    def test_navigate_returns_title_and_text(self):
        from jarvis.browser import handlers

        # Reset module-level state
        handlers._browser = None
        handlers._context = None
        handlers._pw = None

        mock_sync, mock_pw, _, _, mock_page = _mock_playwright()

        with patch("jarvis.browser.handlers.sync_playwright", mock_sync):
            result = handlers.browser_navigate("https://example.com")

        assert result["title"] == "Example Page"
        assert result["url"] == "https://example.com"
        assert "Hello world content" in result["text"]
        mock_page.goto.assert_called_once()
        mock_page.close.assert_called_once()

    def test_truncates_long_text(self):
        from jarvis.browser import handlers

        handlers._browser = None
        handlers._context = None
        handlers._pw = None

        mock_sync, mock_pw, _, _, mock_page = _mock_playwright()
        mock_page.inner_text.return_value = "x" * 20000

        with patch("jarvis.browser.handlers.sync_playwright", mock_sync):
            result = handlers.browser_navigate("https://example.com")

        assert len(result["text"]) == 10000


class TestBrowserScreenshot:
    def test_saves_png_returns_path(self):
        from jarvis.browser import handlers

        handlers._browser = None
        handlers._context = None
        handlers._pw = None

        mock_sync, mock_pw, _, _, mock_page = _mock_playwright()

        with patch("jarvis.browser.handlers.sync_playwright", mock_sync):
            result = handlers.browser_screenshot("https://example.com")

        assert result["title"] == "Example Page"
        assert result["path"].endswith(".png")
        mock_page.screenshot.assert_called_once()
        mock_page.close.assert_called_once()


class TestBrowserExtract:
    def test_extracts_text_from_selector(self):
        from jarvis.browser import handlers

        handlers._browser = None
        handlers._context = None
        handlers._pw = None

        mock_sync, mock_pw, _, _, mock_page = _mock_playwright()
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Extracted text"
        mock_page.query_selector_all.return_value = [mock_element]

        with patch("jarvis.browser.handlers.sync_playwright", mock_sync):
            result = handlers.browser_extract(
                "https://example.com", "h1.title"
            )

        assert "Extracted text" in result["text"]
        assert result["count"] == 1
        mock_page.close.assert_called_once()


class TestBrowserLazyInit:
    def test_reuses_existing_context(self):
        from jarvis.browser import handlers

        handlers._browser = None
        handlers._context = None
        handlers._pw = None

        mock_sync, mock_pw, mock_browser, _, mock_page = _mock_playwright()

        with patch("jarvis.browser.handlers.sync_playwright", mock_sync):
            handlers.browser_navigate("https://one.com")
            handlers.browser_navigate("https://two.com")

        # Chromium.launch called only once (reused)
        mock_pw.chromium.launch.assert_called_once()
