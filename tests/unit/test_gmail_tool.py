from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGmailSearchTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gmail import gmail_search

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"id": "m1", "subject": "Hello", "from": "a@b.com"}]
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gmail_search("test query", 5)

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gmail/search" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["query"] == "test query"
        assert "results" in result.lower() or "m1" in result


class TestGmailReadTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gmail import gmail_read

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "id": "m1",
            "subject": "Hello",
            "from": "a@b.com",
            "body": "Content here",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gmail_read("m1")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gmail/read" in url
        assert "Hello" in result


class TestGmailSendTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gmail import gmail_send

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"id": "sent-1", "thread_id": "t1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gmail_send("bob@example.com", "Hi", "Body")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gmail/send" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["to"] == "bob@example.com"
        assert "sent" in result.lower() or "sent-1" in result


class TestGmailDraftTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gmail import gmail_draft

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"id": "draft-1", "message_id": "md1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gmail_draft("carol@example.com", "Draft", "Body")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gmail/draft" in url
        assert "draft" in result.lower() or "draft-1" in result
