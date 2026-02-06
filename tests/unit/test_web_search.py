from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestWebSearch:
    def test_formats_results(self, monkeypatch):
        from jarvis.tools.web_search import web_search

        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": None,
            "results": [
                {
                    "title": "Python 3.13 Release",
                    "url": "https://python.org/3.13",
                    "content": "Python 3.13 was released on October 2024.",
                },
                {
                    "title": "What's New",
                    "url": "https://docs.python.org/whatsnew",
                    "content": "New features in Python 3.13.",
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = web_search("Python 3.13 release")

        assert "Python 3.13 Release" in result
        assert "https://python.org/3.13" in result
        assert "What's New" in result
        mock_post.assert_called_once()

    def test_includes_answer(self, monkeypatch):
        from jarvis.tools.web_search import web_search

        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Python 3.13 was released in October 2024.",
            "results": [
                {
                    "title": "Python Release",
                    "url": "https://python.org",
                    "content": "Details here.",
                },
            ],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            result = web_search("Python 3.13")

        assert "Summary: Python 3.13 was released in October 2024." in result

    def test_missing_api_key(self, monkeypatch):
        from jarvis.tools.web_search import web_search

        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        result = web_search("test query")
        assert "ERROR" in result
        assert "TAVILY_API_KEY" in result

    def test_handles_empty_results(self, monkeypatch):
        from jarvis.tools.web_search import web_search

        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": None,
            "results": [],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_response):
            result = web_search("obscure query")

        assert "No results found" in result
