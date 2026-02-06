from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_calendar_service():
    """Create a mock Google Calendar API service."""
    return MagicMock()


class TestGcalListHandler:
    def test_list_returns_events(self):
        from jarvis.google.handlers import gcal_list_events

        service = _mock_calendar_service()
        service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "evt1",
                    "summary": "Team standup",
                    "start": {"dateTime": "2026-02-05T09:00:00Z"},
                    "end": {"dateTime": "2026-02-05T09:30:00Z"},
                    "location": "Room A",
                },
            ],
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            results = gcal_list_events(days_ahead=1)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "evt1"
        assert results[0]["summary"] == "Team standup"


class TestGcalCreateHandler:
    def test_create_event(self):
        from jarvis.google.handlers import gcal_create_event

        service = _mock_calendar_service()
        service.events().insert().execute.return_value = {
            "id": "new-evt",
            "htmlLink": "https://calendar.google.com/event/new-evt",
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            result = gcal_create_event(
                summary="Lunch",
                start_time="2026-02-05T12:00:00Z",
                end_time="2026-02-05T13:00:00Z",
            )

        assert result["id"] == "new-evt"
        service.events().insert.assert_called()


class TestGcalUpdateHandler:
    def test_update_event(self):
        from jarvis.google.handlers import gcal_update_event

        service = _mock_calendar_service()
        service.events().patch().execute.return_value = {
            "id": "evt1",
            "htmlLink": "https://calendar.google.com/event/evt1",
        }

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            result = gcal_update_event(event_id="evt1", summary="Updated standup")

        assert result["id"] == "evt1"
        service.events().patch.assert_called()


class TestGcalDeleteHandler:
    def test_delete_event(self):
        from jarvis.google.handlers import gcal_delete_event

        service = _mock_calendar_service()
        service.events().delete().execute.return_value = None

        with patch("jarvis.google.handlers.get_credentials"), patch(
            "jarvis.google.handlers.build", return_value=service
        ):
            result = gcal_delete_event(event_id="evt1")

        assert result["status"] == "deleted"
        service.events().delete.assert_called()
