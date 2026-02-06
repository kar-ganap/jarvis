from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGcalListTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gcal import gcal_list_events

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "events": [{"id": "e1", "summary": "Standup"}]
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gcal_list_events(1)

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gcal/list" in url
        assert "Standup" in result


class TestGcalCreateTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gcal import gcal_create_event

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "id": "new-e",
            "html_link": "https://calendar.google.com/event/new-e",
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gcal_create_event("Lunch", "2026-02-05T12:00:00Z", "2026-02-05T13:00:00Z")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gcal/create" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["summary"] == "Lunch"
        assert "created" in result.lower() or "new-e" in result


class TestGcalUpdateTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gcal import gcal_update_event

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"id": "e1", "html_link": "https://cal/e1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gcal_update_event("e1", "Updated Standup")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gcal/update" in url
        assert "updated" in result.lower() or "e1" in result


class TestGcalDeleteTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gcal import gcal_delete_event

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"status": "deleted"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gcal_delete_event("e1")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/gcal/delete" in url
        assert "deleted" in result.lower()
