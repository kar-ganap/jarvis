from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_docs_service():
    """Create a mock Google Docs API service."""
    return MagicMock()


def _mock_drive_service():
    """Create a mock Google Drive API service."""
    return MagicMock()


class TestGdocsList:
    def test_returns_documents(self):
        from jarvis.google.docs_handlers import gdocs_list

        drive = _mock_drive_service()
        drive.files().list().execute.return_value = {
            "files": [
                {
                    "id": "doc-1",
                    "name": "Meeting Notes",
                    "modifiedTime": "2026-01-15T10:00:00Z",
                    "webViewLink": "https://docs.google.com/document/d/doc-1",
                },
            ],
        }

        with patch("jarvis.google.docs_handlers.get_credentials"), \
             patch("jarvis.google.docs_handlers.build", return_value=drive):
            results = gdocs_list(max_results=5)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "doc-1"
        assert results[0]["name"] == "Meeting Notes"

    def test_empty_results(self):
        from jarvis.google.docs_handlers import gdocs_list

        drive = _mock_drive_service()
        drive.files().list().execute.return_value = {"files": []}

        with patch("jarvis.google.docs_handlers.get_credentials"), \
             patch("jarvis.google.docs_handlers.build", return_value=drive):
            results = gdocs_list()

        assert results == []


class TestGdocsRead:
    def test_reads_document_text(self):
        from jarvis.google.docs_handlers import gdocs_read

        docs = _mock_docs_service()
        docs.documents().get().execute.return_value = {
            "title": "My Document",
            "body": {
                "content": [
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Hello world\n"}},
                            ]
                        }
                    },
                    {
                        "paragraph": {
                            "elements": [
                                {"textRun": {"content": "Second paragraph\n"}},
                            ]
                        }
                    },
                ]
            },
        }

        with patch("jarvis.google.docs_handlers.get_credentials"), \
             patch("jarvis.google.docs_handlers.build", return_value=docs):
            result = gdocs_read("doc-1")

        assert result["id"] == "doc-1"
        assert result["title"] == "My Document"
        assert "Hello world" in result["content"]
        assert "Second paragraph" in result["content"]

    def test_reads_empty_document(self):
        from jarvis.google.docs_handlers import gdocs_read

        docs = _mock_docs_service()
        docs.documents().get().execute.return_value = {
            "title": "Empty Doc",
            "body": {"content": []},
        }

        with patch("jarvis.google.docs_handlers.get_credentials"), \
             patch("jarvis.google.docs_handlers.build", return_value=docs):
            result = gdocs_read("doc-2")

        assert result["title"] == "Empty Doc"
        assert result["content"] == ""


class TestGdocsCreate:
    def test_creates_document(self):
        from jarvis.google.docs_handlers import gdocs_create

        docs = _mock_docs_service()
        docs.documents().create().execute.return_value = {
            "documentId": "new-doc-1",
            "title": "My New Doc",
        }

        with patch("jarvis.google.docs_handlers.get_credentials"), \
             patch("jarvis.google.docs_handlers.build", return_value=docs):
            result = gdocs_create("My New Doc")

        assert result["id"] == "new-doc-1"
        assert result["title"] == "My New Doc"


class TestGdocsAppend:
    def test_appends_text(self):
        from jarvis.google.docs_handlers import gdocs_append

        docs = _mock_docs_service()
        # get() returns doc with endIndex for calculating insertion point
        docs.documents().get().execute.return_value = {
            "body": {
                "content": [
                    {"endIndex": 50},
                ]
            }
        }
        docs.documents().batchUpdate().execute.return_value = {}

        with patch("jarvis.google.docs_handlers.get_credentials"), \
             patch("jarvis.google.docs_handlers.build", return_value=docs):
            result = gdocs_append("doc-1", "Appended text")

        assert result["status"] == "appended"
        docs.documents().batchUpdate.assert_called()
