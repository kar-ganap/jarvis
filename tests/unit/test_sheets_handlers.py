from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_sheets_service():
    """Create a mock Google Sheets API service."""
    return MagicMock()


def _mock_drive_service():
    """Create a mock Google Drive API service."""
    return MagicMock()


class TestGsheetsList:
    def test_returns_spreadsheets(self):
        from jarvis.google.sheets_handlers import gsheets_list

        drive = _mock_drive_service()
        drive.files().list().execute.return_value = {
            "files": [
                {
                    "id": "sheet-1",
                    "name": "Budget 2026",
                    "modifiedTime": "2026-01-20T14:30:00Z",
                    "webViewLink": "https://docs.google.com/spreadsheets/d/sheet-1",
                },
            ],
        }

        with patch("jarvis.google.sheets_handlers.get_credentials"), \
             patch("jarvis.google.sheets_handlers.build", return_value=drive):
            results = gsheets_list(max_results=5)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "sheet-1"
        assert results[0]["name"] == "Budget 2026"

    def test_empty_results(self):
        from jarvis.google.sheets_handlers import gsheets_list

        drive = _mock_drive_service()
        drive.files().list().execute.return_value = {"files": []}

        with patch("jarvis.google.sheets_handlers.get_credentials"), \
             patch("jarvis.google.sheets_handlers.build", return_value=drive):
            results = gsheets_list()

        assert results == []


class TestGsheetsRead:
    def test_reads_values(self):
        from jarvis.google.sheets_handlers import gsheets_read

        sheets = _mock_sheets_service()
        sheets.spreadsheets().values().get().execute.return_value = {
            "range": "Sheet1!A1:C3",
            "values": [
                ["Name", "Age", "City"],
                ["Alice", "30", "NYC"],
                ["Bob", "25", "LA"],
            ],
        }

        with patch("jarvis.google.sheets_handlers.get_credentials"), \
             patch("jarvis.google.sheets_handlers.build", return_value=sheets):
            result = gsheets_read("sheet-1", range_str="Sheet1!A1:C3")

        assert result["spreadsheet_id"] == "sheet-1"
        assert len(result["values"]) == 3
        assert result["values"][0] == ["Name", "Age", "City"]

    def test_reads_empty_sheet(self):
        from jarvis.google.sheets_handlers import gsheets_read

        sheets = _mock_sheets_service()
        sheets.spreadsheets().values().get().execute.return_value = {
            "range": "Sheet1",
        }

        with patch("jarvis.google.sheets_handlers.get_credentials"), \
             patch("jarvis.google.sheets_handlers.build", return_value=sheets):
            result = gsheets_read("sheet-2")

        assert result["values"] == []


class TestGsheetsCreate:
    def test_creates_spreadsheet(self):
        from jarvis.google.sheets_handlers import gsheets_create

        sheets = _mock_sheets_service()
        sheets.spreadsheets().create().execute.return_value = {
            "spreadsheetId": "new-sheet-1",
            "properties": {"title": "New Budget"},
            "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/new-sheet-1",
        }

        with patch("jarvis.google.sheets_handlers.get_credentials"), \
             patch("jarvis.google.sheets_handlers.build", return_value=sheets):
            result = gsheets_create("New Budget")

        assert result["id"] == "new-sheet-1"
        assert result["title"] == "New Budget"


class TestGsheetsAppend:
    def test_appends_rows(self):
        import json

        from jarvis.google.sheets_handlers import gsheets_append

        sheets = _mock_sheets_service()
        sheets.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 2},
        }

        values_json = json.dumps([["Charlie", "35", "SF"], ["Diana", "28", "Boston"]])

        with patch("jarvis.google.sheets_handlers.get_credentials"), \
             patch("jarvis.google.sheets_handlers.build", return_value=sheets):
            result = gsheets_append("sheet-1", "Sheet1", values_json)

        assert result["updated_rows"] == 2
