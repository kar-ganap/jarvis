from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestCreateReminder:
    def test_posts_to_bridge(self, monkeypatch):
        from jarvis.tools.scheduler_tool import create_reminder

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"status": "added", "id": "rem-1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = create_reminder("check PR", 5)

        assert "OK" in result
        assert "5 minutes" in result
        call_json = mock_post.call_args[1]["json"]
        assert call_json["type"] == "reminder"
        assert call_json["delay_seconds"] == 300
        assert call_json["context"] == "check PR"


class TestCreateRecurringJob:
    def test_posts_to_bridge(self, monkeypatch):
        from jarvis.tools.scheduler_tool import create_recurring_job

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"status": "added", "id": "cron-1"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = create_recurring_job("morning briefing", "0 8 * * *")

        assert "OK" in result
        call_json = mock_post.call_args[1]["json"]
        assert call_json["type"] == "cron"
        assert call_json["cron"] == "0 8 * * *"


class TestListScheduledJobs:
    def test_formats_jobs(self, monkeypatch):
        from jarvis.tools.scheduler_tool import list_scheduled_jobs

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "jobs": [
                {"id": "rem-1", "next_run": "2026-01-01", "trigger": "date"},
            ]
        }

        with patch("requests.get", return_value=mock_resp):
            result = list_scheduled_jobs()

        assert "rem-1" in result
        assert "1" in result  # count

    def test_empty_list(self, monkeypatch):
        from jarvis.tools.scheduler_tool import list_scheduled_jobs

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"jobs": []}

        with patch("requests.get", return_value=mock_resp):
            result = list_scheduled_jobs()

        assert "No scheduled jobs" in result


class TestRemoveScheduledJob:
    def test_posts_to_bridge(self, monkeypatch):
        from jarvis.tools.scheduler_tool import remove_scheduled_job

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"status": "removed"}

        with patch("requests.post", return_value=mock_resp):
            result = remove_scheduled_job("rem-1")

        assert "removed" in result.lower()
