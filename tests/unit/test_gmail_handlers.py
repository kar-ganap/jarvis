from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch


def _mock_gmail_service():
    """Create a mock Gmail API service."""
    service = MagicMock()
    return service


class TestGmailSearchHandler:
    def test_search_returns_results(self):
        from jarvis.google.handlers import gmail_search

        service = _mock_gmail_service()
        service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}],
        }
        service.users().messages().get().execute.return_value = {
            "id": "msg1",
            "snippet": "Hey there",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Date", "value": "2026-01-15"},
                ],
            },
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            results = gmail_search("test query", max_results=5)

        assert isinstance(results, list)
        assert len(results) > 0
        assert "id" in results[0]


class TestGmailReadHandler:
    def test_read_returns_email(self):
        from jarvis.google.handlers import gmail_read

        service = _mock_gmail_service()
        body_text = base64.urlsafe_b64encode(b"Hello, world!").decode()
        service.users().messages().get().execute.return_value = {
            "id": "msg1",
            "snippet": "Hello",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test"},
                    {"name": "From", "value": "bob@example.com"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Date", "value": "2026-01-15"},
                ],
                "body": {"data": body_text},
            },
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            result = gmail_read("msg1")

        assert result["id"] == "msg1"
        assert result["subject"] == "Test"
        assert "Hello, world!" in result["body"]


class TestGmailSendHandler:
    def test_send_creates_and_sends(self):
        from jarvis.google.handlers import gmail_send

        service = _mock_gmail_service()
        service.users().messages().send().execute.return_value = {
            "id": "sent-1",
            "threadId": "thread-1",
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            result = gmail_send("bob@example.com", "Hi", "Body text")

        assert result["id"] == "sent-1"
        service.users().messages().send.assert_called()


class TestGmailDraftHandler:
    def test_draft_creates_draft(self):
        from jarvis.google.handlers import gmail_draft

        service = _mock_gmail_service()
        service.users().drafts().create().execute.return_value = {
            "id": "draft-1",
            "message": {"id": "msg-draft-1"},
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            result = gmail_draft("carol@example.com", "Draft Subject", "Draft body")

        assert result["id"] == "draft-1"
        service.users().drafts().create.assert_called()
