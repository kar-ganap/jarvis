from __future__ import annotations

from googleapiclient.discovery import build

from jarvis.google.auth import get_credentials


def _docs_service():
    """Build and return a Google Docs API service."""
    creds = get_credentials()
    return build("docs", "v1", credentials=creds)


def _drive_service():
    """Build and return a Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def gdocs_list(max_results: int = 10) -> list[dict]:
    """List Google Docs documents from Drive."""
    service = _drive_service()
    result = service.files().list(
        q="mimeType='application/vnd.google-apps.document'",
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


def gdocs_read(document_id: str) -> dict:
    """Read text content from a Google Doc."""
    service = _docs_service()
    doc = service.documents().get(documentId=document_id).execute()

    texts = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun", {})
                content = text_run.get("content", "")
                if content:
                    texts.append(content)

    return {
        "id": document_id,
        "title": doc.get("title", ""),
        "content": "".join(texts).strip(),
    }


def gdocs_create(title: str) -> dict:
    """Create a new blank Google Doc."""
    service = _docs_service()
    doc = service.documents().create(body={"title": title}).execute()
    return {
        "id": doc["documentId"],
        "title": title,
    }


def gdocs_append(document_id: str, text: str) -> dict:
    """Append text to the end of a Google Doc."""
    service = _docs_service()

    # Get current doc to find end index
    doc = service.documents().get(documentId=document_id).execute()
    body_content = doc.get("body", {}).get("content", [])
    end_index = 1  # default
    if body_content:
        end_index = body_content[-1].get("endIndex", 1)

    # Insert at end of body (index - 1 to stay inside body segment)
    insert_index = max(end_index - 1, 1)

    requests = [
        {
            "insertText": {
                "location": {"index": insert_index},
                "text": text,
            }
        }
    ]

    service.documents().batchUpdate(
        documentId=document_id,
        body={"requests": requests},
    ).execute()

    return {"status": "appended", "document_id": document_id}
