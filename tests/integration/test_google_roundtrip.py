"""Integration tests for Gmail + Google Calendar.

These tests call real Google APIs using the OAuth token from setup_google_oauth.py.
They are skipped if the token file doesn't exist.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Skip all tests if no Google token is available
_token_path = os.environ.get(
    "GOOGLE_TOKEN_PATH",
    str(Path(__file__).resolve().parent.parent.parent / "google_token.json"),
)
pytestmark = pytest.mark.skipif(
    not Path(_token_path).exists(),
    reason="Google OAuth token not found — run scripts/setup_google_oauth.py",
)


@pytest.fixture(autouse=True)
def _set_token_env(monkeypatch):
    """Ensure GOOGLE_TOKEN_PATH is set for handlers."""
    monkeypatch.setenv("GOOGLE_TOKEN_PATH", _token_path)


class TestGmailIntegration:
    def test_search_returns_results(self):
        """Search for recent emails — should return a non-error response."""
        from jarvis.google.handlers import gmail_search

        results = gmail_search("in:inbox", max_results=2)
        assert isinstance(results, list)
        # Might be empty if inbox is empty, but should not raise

    def test_read_email(self):
        """Search for one email and read it."""
        from jarvis.google.handlers import gmail_read, gmail_search

        results = gmail_search("in:inbox", max_results=1)
        if not results:
            pytest.skip("No emails in inbox to read")
        msg = gmail_read(results[0]["id"])
        assert "id" in msg
        assert "subject" in msg
        assert "body" in msg


class TestGcalIntegration:
    def test_list_events(self):
        """List events for the next 7 days — should return a list."""
        from jarvis.google.handlers import gcal_list_events

        events = gcal_list_events(days_ahead=7)
        assert isinstance(events, list)
        # Might be empty, but should not raise
