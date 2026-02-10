from __future__ import annotations


def todoist_list_tasks(project_id: str = "", filter_str: str = "") -> str:
    """List active Todoist tasks, optionally filtered.

    Args:
        project_id: Optional project ID to filter tasks by.
        filter_str: Optional Todoist filter string (e.g. 'today', 'overdue').

    Returns:
        Formatted list of tasks with IDs, content, due dates, and priorities.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/todoist/tasks",
        json={"project_id": project_id, "filter_str": filter_str},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No tasks found."
    lines = []
    for t in results:
        due = f" (due: {t['due']})" if t.get("due") else ""
        pri = f" P{t.get('priority', 1)}"
        lines.append(f"  [{t['id']}] {t['content']}{due}{pri}")
    return f"Found {len(results)} tasks:\n" + "\n".join(lines)


def todoist_create_task(
    content: str, project_id: str = "", due_string: str = "", priority: int = 1,
) -> str:
    """Create a new Todoist task.

    Args:
        content: Task content/title.
        project_id: Optional project ID to add the task to.
        due_string: Optional due date string (e.g. 'tomorrow', 'every monday').
        priority: Task priority (1=normal, 4=urgent).

    Returns:
        Confirmation with task ID and URL.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/todoist/tasks/create",
        json={
            "content": content,
            "project_id": project_id,
            "due_string": due_string,
            "priority": priority,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return f"Created task '{data.get('content', content)}' (id: {data.get('id', 'unknown')})"


def todoist_complete_task(task_id: str) -> str:
    """Complete (close) a Todoist task.

    Args:
        task_id: The ID of the task to complete.

    Returns:
        Confirmation that the task was completed.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/todoist/tasks/complete",
        json={"task_id": task_id},
        timeout=30,
    )
    resp.raise_for_status()
    return f"Completed task {task_id}"


def todoist_list_projects() -> str:
    """List all Todoist projects.

    Returns:
        Formatted list of projects with IDs and names.
    """
    import os

    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    resp = requests.post(
        f"http://{host}:{port}/todoist/projects",
        json={},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return "No projects found."
    lines = []
    for p in results:
        lines.append(f"  [{p['id']}] {p['name']}")
    return f"Found {len(results)} projects:\n" + "\n".join(lines)


TOOLS = [todoist_list_tasks, todoist_create_task, todoist_complete_task, todoist_list_projects]
