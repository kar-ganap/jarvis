from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestNotionSearchTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.notion import notion_search

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"id": "page-1", "title": "Notes", "type": "page"}]
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = notion_search("notes", 10)

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/notion/search" in url
        assert "Notes" in result


class TestNotionReadPageTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.notion import notion_read_page

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "id": "page-1",
            "title": "My Page",
            "content": "Hello world",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = notion_read_page("page-1")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/notion/read" in url
        assert "Hello world" in result


class TestNotionCreatePageTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.notion import notion_create_page

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "id": "new-page",
            "url": "https://notion.so/new-page",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = notion_create_page("parent-1", "Test Page", "content")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/notion/create" in url
        assert "new-page" in result


class TestNotionAppendBlocksTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.notion import notion_append_blocks

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"block_count": 2}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = notion_append_blocks("page-1", "Some text")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/notion/append" in url
        assert "2" in result


class TestNotionQueryDatabaseTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.notion import notion_query_database

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"id": "row-1", "title": "Task 1"}]
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = notion_query_database("db-1", '{"property": "Status"}')

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/notion/query_db" in url
        assert "Task 1" in result
