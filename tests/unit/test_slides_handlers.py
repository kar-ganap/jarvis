from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_slides_service():
    """Create a mock Google Slides API service."""
    return MagicMock()


def _mock_drive_service():
    """Create a mock Google Drive API service."""
    return MagicMock()


class TestGslidesList:
    def test_list_presentations(self):
        from jarvis.google.slides_handlers import gslides_list

        service = _mock_drive_service()
        service.files().list().execute.return_value = {
            "files": [
                {
                    "id": "pres1",
                    "name": "Q4 Review",
                    "modifiedTime": "2026-01-15T10:00:00Z",
                    "webViewLink": "https://docs.google.com/presentation/d/pres1",
                },
            ],
        }

        with patch("jarvis.google.slides_handlers.get_credentials"), patch(
            "jarvis.google.slides_handlers.build", return_value=service
        ):
            results = gslides_list(max_results=10)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "pres1"
        assert results[0]["name"] == "Q4 Review"


class TestGslidesRead:
    def test_reads_slide_text(self):
        from jarvis.google.slides_handlers import gslides_read

        service = _mock_slides_service()
        service.presentations().get().execute.return_value = {
            "presentationId": "pres1",
            "title": "Q4 Review",
            "slides": [
                {
                    "pageElements": [
                        {
                            "shape": {
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "Slide 1 Title\n"}},
                                        {"textRun": {"content": "Some body text"}},
                                    ]
                                }
                            }
                        }
                    ]
                },
            ],
        }

        with patch("jarvis.google.slides_handlers.get_credentials"), patch(
            "jarvis.google.slides_handlers.build", return_value=service
        ):
            result = gslides_read("pres1")

        assert result["id"] == "pres1"
        assert result["title"] == "Q4 Review"
        assert len(result["slides"]) == 1
        assert "Slide 1 Title" in result["slides"][0]["text"]
        assert "Some body text" in result["slides"][0]["text"]


class TestGslidesCreate:
    def test_creates_presentation(self):
        from jarvis.google.slides_handlers import gslides_create

        service = _mock_slides_service()
        service.presentations().create().execute.return_value = {
            "presentationId": "new-pres",
            "title": "My Deck",
        }

        with patch("jarvis.google.slides_handlers.get_credentials"), patch(
            "jarvis.google.slides_handlers.build", return_value=service
        ):
            result = gslides_create("My Deck")

        assert result["id"] == "new-pres"
        assert result["title"] == "My Deck"
        service.presentations().create.assert_called()


class TestGslidesAddSlide:
    def test_adds_slide_with_text(self):
        from jarvis.google.slides_handlers import gslides_add_slide

        service = _mock_slides_service()
        service.presentations().batchUpdate().execute.return_value = {
            "replies": [{"createSlide": {"objectId": "slide-abc"}}]
        }

        with patch("jarvis.google.slides_handlers.get_credentials"), patch(
            "jarvis.google.slides_handlers.build", return_value=service
        ):
            result = gslides_add_slide("pres1", "New Slide", "Content here")

        assert result["slide_id"] == "slide-abc"
        service.presentations().batchUpdate.assert_called()
