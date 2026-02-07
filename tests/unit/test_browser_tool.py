from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestBrowserNavigateTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.browser import browser_navigate

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "title": "Example Page",
            "url": "https://example.com",
            "text": "Hello world",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = browser_navigate("https://example.com")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/browser/navigate" in url
        assert "Example Page" in result
        assert "Hello world" in result


class TestBrowserScreenshotTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.browser import browser_screenshot

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "title": "Example Page",
            "path": "/tmp/jarvis_screenshot_abc.png",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = browser_screenshot("https://example.com")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/browser/screenshot" in url
        assert ".png" in result


class TestBrowserExtractTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.browser import browser_extract

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "text": "Extracted content",
            "count": 2,
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = browser_extract("https://example.com", "div.content")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/browser/extract" in url
        assert "Extracted content" in result
