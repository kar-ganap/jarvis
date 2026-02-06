from __future__ import annotations

import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from jarvis.google.auth import get_credentials


def _gmail_service():
    """Build and return a Gmail API service."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def _calendar_service():
    """Build and return a Google Calendar API service."""
    creds = get_credentials()
    return build("calendar", "v3", credentials=creds)


def _get_header(headers: list[dict], name: str) -> str:
    """Extract a header value by name from Gmail message headers."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode_body(payload: dict) -> str:
    """Decode the email body from a Gmail message payload."""
    # Direct body data
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Multipart: find text/plain part
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                "utf-8", errors="replace"
            )

    return "(no text body)"


# --- Gmail handlers ---


def gmail_search(query: str, max_results: int = 5) -> list[dict]:
    """Search Gmail messages matching the query string."""
    service = _gmail_service()
    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    results = []
    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()
        headers = msg.get("payload", {}).get("headers", [])
        results.append({
            "id": msg["id"],
            "subject": _get_header(headers, "Subject"),
            "from": _get_header(headers, "From"),
            "date": _get_header(headers, "Date"),
            "snippet": msg.get("snippet", ""),
        })
    return results


def gmail_read(message_id: str) -> dict:
    """Read a single Gmail message by ID."""
    service = _gmail_service()
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    headers = msg.get("payload", {}).get("headers", [])
    body = _decode_body(msg.get("payload", {}))

    return {
        "id": msg["id"],
        "subject": _get_header(headers, "Subject"),
        "from": _get_header(headers, "From"),
        "to": _get_header(headers, "To"),
        "date": _get_header(headers, "Date"),
        "body": body,
    }


def gmail_send(to: str, subject: str, body: str) -> dict:
    """Compose and send an email."""
    service = _gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    return {"id": result["id"], "thread_id": result.get("threadId", "")}


def gmail_draft(to: str, subject: str, body: str) -> dict:
    """Create a draft email."""
    service = _gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()

    return {"id": result["id"], "message_id": result.get("message", {}).get("id", "")}


# --- Calendar handlers ---


def gcal_list_events(days_ahead: int = 1) -> list[dict]:
    """List calendar events for the next N days."""
    from datetime import UTC, datetime, timedelta

    service = _calendar_service()
    now = datetime.now(tz=UTC)
    time_max = now + timedelta(days=days_ahead)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for evt in result.get("items", []):
        events.append({
            "id": evt["id"],
            "summary": evt.get("summary", "(no title)"),
            "start": evt.get("start", {}).get("dateTime", evt.get("start", {}).get("date", "")),
            "end": evt.get("end", {}).get("dateTime", evt.get("end", {}).get("date", "")),
            "location": evt.get("location", ""),
        })
    return events


def gcal_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
) -> dict:
    """Create a new calendar event."""
    service = _calendar_service()
    event_body: dict = {
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location

    result = service.events().insert(
        calendarId="primary", body=event_body
    ).execute()

    return {"id": result["id"], "html_link": result.get("htmlLink", "")}


def gcal_update_event(
    event_id: str,
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
) -> dict:
    """Update an existing calendar event (partial update)."""
    service = _calendar_service()
    body: dict = {}
    if summary:
        body["summary"] = summary
    if start_time:
        body["start"] = {"dateTime": start_time}
    if end_time:
        body["end"] = {"dateTime": end_time}
    if description:
        body["description"] = description
    if location:
        body["location"] = location

    result = service.events().patch(
        calendarId="primary", eventId=event_id, body=body
    ).execute()

    return {"id": result["id"], "html_link": result.get("htmlLink", "")}


def gcal_delete_event(event_id: str) -> dict:
    """Delete a calendar event by ID."""
    service = _calendar_service()
    service.events().delete(
        calendarId="primary", eventId=event_id
    ).execute()

    return {"status": "deleted"}
