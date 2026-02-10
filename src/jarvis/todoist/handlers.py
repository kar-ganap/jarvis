from __future__ import annotations

import os

import requests

_BASE_URL = "https://api.todoist.com/rest/v2"


def _todoist_headers() -> dict:
    """Build Authorization header from TODOIST_API_KEY env var."""
    api_key = os.environ.get("TODOIST_API_KEY", "")
    if not api_key:
        raise ValueError(
            "TODOIST_API_KEY environment variable not set. "
            "Get your API token from https://todoist.com/app/settings/integrations/developer"
        )
    return {"Authorization": f"Bearer {api_key}"}


def todoist_list_tasks(
    project_id: str = "", filter_str: str = "",
) -> list[dict]:
    """List active tasks, optionally filtered by project or filter string."""
    headers = _todoist_headers()
    params: dict = {}
    if project_id:
        params["project_id"] = project_id
    if filter_str:
        params["filter"] = filter_str

    resp = requests.get(f"{_BASE_URL}/tasks", headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    tasks = resp.json()
    return [
        {
            "id": t["id"],
            "content": t["content"],
            "due": t.get("due", {}).get("string", "") if t.get("due") else "",
            "priority": t.get("priority", 1),
            "project_id": t.get("project_id", ""),
        }
        for t in tasks
    ]


def todoist_create_task(
    content: str,
    project_id: str = "",
    due_string: str = "",
    priority: int = 1,
) -> dict:
    """Create a new task."""
    headers = _todoist_headers()
    body: dict = {"content": content, "priority": priority}
    if project_id:
        body["project_id"] = project_id
    if due_string:
        body["due_string"] = due_string

    resp = requests.post(f"{_BASE_URL}/tasks", headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    t = resp.json()
    return {
        "id": t["id"],
        "content": t["content"],
        "due": t.get("due", {}).get("string", "") if t.get("due") else "",
        "priority": t.get("priority", 1),
        "url": t.get("url", ""),
    }


def todoist_complete_task(task_id: str) -> dict:
    """Close (complete) a task by ID."""
    headers = _todoist_headers()
    resp = requests.post(f"{_BASE_URL}/tasks/{task_id}/close", headers=headers, timeout=30)
    resp.raise_for_status()
    return {"status": "completed", "task_id": task_id}


def todoist_list_projects() -> list[dict]:
    """List all projects."""
    headers = _todoist_headers()
    resp = requests.get(f"{_BASE_URL}/projects", headers=headers, timeout=30)
    resp.raise_for_status()
    projects = resp.json()
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "color": p.get("color", ""),
        }
        for p in projects
    ]
