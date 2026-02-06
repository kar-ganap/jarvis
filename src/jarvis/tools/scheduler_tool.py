from __future__ import annotations


def create_reminder(
    text: str,
    delay_minutes: int,
    notify_channel: str = "",
    notify_recipient: str = "",
) -> str:
    """Create a one-time reminder that fires after the specified delay.

    Args:
        text: The reminder text / context.
        delay_minutes: Minutes until the reminder fires.
        notify_channel: Channel to notify on when the reminder fires (e.g. 'slack').
        notify_recipient: Recipient ID for the notification (e.g. user's channel ID).

    Returns:
        Confirmation with the job ID.
    """
    import os
    import uuid

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    job_id = f"reminder-{uuid.uuid4().hex[:8]}"
    resp = requests.post(
        f"http://{host}:{port}/scheduler/add",
        json={
            "type": "reminder",
            "id": job_id,
            "context": text,
            "delay_seconds": delay_minutes * 60,
            "notify_channel": notify_channel,
            "notify_recipient": notify_recipient,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return f"OK: Reminder '{text}' set for {delay_minutes} minutes (id: {job_id})"


def create_recurring_job(
    text: str,
    cron_expression: str,
    notify_channel: str = "",
    notify_recipient: str = "",
) -> str:
    """Create a recurring scheduled job using a cron expression.

    Args:
        text: Description/context sent to the agent on each trigger.
        cron_expression: Standard 5-field cron (e.g., '0 8 * * *' for 8am daily).
        notify_channel: Channel to notify on when the job fires (e.g. 'slack').
        notify_recipient: Recipient ID for the notification (e.g. user's channel ID).

    Returns:
        Confirmation with the job ID.
    """
    import os
    import uuid

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    job_id = f"cron-{uuid.uuid4().hex[:8]}"
    resp = requests.post(
        f"http://{host}:{port}/scheduler/add",
        json={
            "type": "cron",
            "id": job_id,
            "context": text,
            "cron": cron_expression,
            "notify_channel": notify_channel,
            "notify_recipient": notify_recipient,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return f"OK: Recurring job '{text}' with cron '{cron_expression}' (id: {job_id})"


def list_scheduled_jobs() -> str:
    """List all currently scheduled jobs.

    Returns:
        A formatted list of scheduled jobs with IDs and next run times.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.get(
        f"http://{host}:{port}/scheduler/list",
        timeout=10,
    )
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    if not jobs:
        return "No scheduled jobs."
    lines = []
    for j in jobs:
        lines.append(f"  {j['id']} — next: {j['next_run']} — {j['trigger']}")
    return f"Scheduled jobs ({len(jobs)}):\n" + "\n".join(lines)


def remove_scheduled_job(job_id: str) -> str:
    """Remove a scheduled job by its ID.

    Args:
        job_id: The job ID to remove.

    Returns:
        Confirmation or error message.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/scheduler/remove",
        json={"id": job_id},
        timeout=10,
    )
    resp.raise_for_status()
    status = resp.json().get("status", "unknown")
    if status == "removed":
        return f"OK: Job '{job_id}' removed."
    return f"Job '{job_id}' not found."


TOOLS = [create_reminder, create_recurring_job, list_scheduled_jobs, remove_scheduled_job]
