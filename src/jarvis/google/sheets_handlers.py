from __future__ import annotations

import json

from googleapiclient.discovery import build

from jarvis.google.auth import get_credentials


def _sheets_service():
    """Build and return a Google Sheets API service."""
    creds = get_credentials()
    return build("sheets", "v4", credentials=creds)


def _drive_service():
    """Build and return a Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def gsheets_list(max_results: int = 10) -> list[dict]:
    """List Google Sheets spreadsheets from Drive."""
    service = _drive_service()
    result = service.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        pageSize=max_results,
        fields="files(id, name, modifiedTime, webViewLink)",
        orderBy="modifiedTime desc",
    ).execute()

    return [
        {
            "id": f["id"],
            "name": f["name"],
            "modified": f.get("modifiedTime", ""),
            "link": f.get("webViewLink", ""),
        }
        for f in result.get("files", [])
    ]


def gsheets_read(spreadsheet_id: str, range_str: str = "Sheet1") -> dict:
    """Read values from a spreadsheet range."""
    service = _sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_str,
    ).execute()

    return {
        "spreadsheet_id": spreadsheet_id,
        "range": result.get("range", range_str),
        "values": result.get("values", []),
    }


def gsheets_create(title: str) -> dict:
    """Create a new spreadsheet."""
    service = _sheets_service()
    body = {"properties": {"title": title}}
    result = service.spreadsheets().create(body=body).execute()
    return {
        "id": result["spreadsheetId"],
        "title": result["properties"]["title"],
        "url": result.get("spreadsheetUrl", ""),
    }


def gsheets_append(
    spreadsheet_id: str, range_str: str, values_json: str,
) -> dict:
    """Append rows to a spreadsheet. values_json is a JSON-encoded list[list]."""
    service = _sheets_service()
    values = json.loads(values_json)

    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    updates = result.get("updates", {})
    return {
        "spreadsheet_id": spreadsheet_id,
        "updated_rows": updates.get("updatedRows", 0),
    }
