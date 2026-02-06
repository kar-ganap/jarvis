from __future__ import annotations


def gcal_list_events(days_ahead: int = 1) -> str:
    """List upcoming Google Calendar events.

    Args:
        days_ahead: Number of days ahead to look for events.

    Returns:
        Formatted list of upcoming events with times and locations.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gcal/list",
        json={"days_ahead": days_ahead},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    events = data.get("events", [])
    if not events:
        return "No upcoming events."
    lines = []
    for e in events:
        loc = f" @ {e['location']}" if e.get("location") else ""
        lines.append(f"  {e.get('start', '')} — {e.get('summary', '(no title)')}{loc}")
    return f"Upcoming events ({len(events)}):\n" + "\n".join(lines)


def gcal_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
) -> str:
    """Create a new Google Calendar event.

    Args:
        summary: Event title.
        start_time: Start time in ISO 8601 format (e.g. '2026-02-05T12:00:00Z').
        end_time: End time in ISO 8601 format.
        description: Optional event description.
        location: Optional event location.

    Returns:
        Confirmation with event ID and link.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gcal/create",
        json={
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "location": location,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Event created: {summary} (id: {data.get('id', 'unknown')})"


def gcal_update_event(
    event_id: str,
    summary: str = "",
    start_time: str = "",
    end_time: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """Update an existing Google Calendar event.

    Args:
        event_id: The event ID to update.
        summary: New event title (leave empty to keep current).
        start_time: New start time in ISO 8601 (leave empty to keep current).
        end_time: New end time in ISO 8601 (leave empty to keep current).
        description: New description (leave empty to keep current).
        location: New location (leave empty to keep current).

    Returns:
        Confirmation with event ID.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gcal/update",
        json={
            "event_id": event_id,
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "location": location,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Event updated (id: {data.get('id', 'unknown')})"


def gcal_delete_event(event_id: str) -> str:
    """Delete a Google Calendar event.

    Args:
        event_id: The event ID to delete.

    Returns:
        Confirmation of deletion.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/google/gcal/delete",
        json={"event_id": event_id},
        timeout=30,
    )
    resp.raise_for_status()
    return f"Event deleted (id: {event_id})"


TOOLS = [gcal_list_events, gcal_create_event, gcal_update_event, gcal_delete_event]
