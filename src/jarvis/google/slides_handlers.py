from __future__ import annotations

import uuid

from googleapiclient.discovery import build

from jarvis.google.auth import get_credentials


def _slides_service():
    """Build and return a Google Slides API service."""
    creds = get_credentials()
    return build("slides", "v1", credentials=creds)


def _drive_service():
    """Build and return a Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def gslides_list(max_results: int = 10) -> list[dict]:
    """List Google Slides presentations from Drive."""
    service = _drive_service()
    result = service.files().list(
        q="mimeType='application/vnd.google-apps.presentation'",
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


def gslides_read(presentation_id: str) -> dict:
    """Read all text content from a presentation's slides."""
    service = _slides_service()
    pres = service.presentations().get(
        presentationId=presentation_id
    ).execute()

    slides_text = []
    for i, slide in enumerate(pres.get("slides", []), 1):
        texts = []
        for element in slide.get("pageElements", []):
            shape = element.get("shape", {})
            text_field = shape.get("text", {})
            for te in text_field.get("textElements", []):
                run = te.get("textRun", {})
                content = run.get("content", "")
                if content:
                    texts.append(content)
        slides_text.append({
            "slide_number": i,
            "text": "".join(texts).strip(),
        })

    return {
        "id": presentation_id,
        "title": pres.get("title", ""),
        "slides": slides_text,
    }


def gslides_create(title: str) -> dict:
    """Create a new blank presentation."""
    service = _slides_service()
    body = {"title": title}
    pres = service.presentations().create(body=body).execute()
    return {
        "id": pres["presentationId"],
        "title": title,
    }


def gslides_add_slide(
    presentation_id: str, title: str, body: str,
) -> dict:
    """Add a new slide with title and body text to a presentation."""
    service = _slides_service()
    slide_id = f"slide_{uuid.uuid4().hex[:8]}"

    requests = [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {
                    "predefinedLayout": "TITLE_AND_BODY",
                },
            },
        },
    ]

    result = service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests},
    ).execute()

    reply_id = slide_id
    for reply in result.get("replies", []):
        create_reply = reply.get("createSlide", {})
        if create_reply.get("objectId"):
            reply_id = create_reply["objectId"]

    return {"slide_id": reply_id}
