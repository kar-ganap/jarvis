"""Phase 9 live validation — Todoist integration.

Usage:
  set -a && source ~/.zshrc && set +a
  uv run python scripts/validate_todoist.py
"""
from __future__ import annotations

import os
import sys

todoist_key = os.environ.get("TODOIST_API_KEY", "")
if not todoist_key:
    print("ERROR: TODOIST_API_KEY not set")
    sys.exit(1)


def validate_todoist():
    from jarvis.todoist.handlers import (
        todoist_complete_task,
        todoist_create_task,
        todoist_list_projects,
        todoist_list_tasks,
    )

    print("=== Todoist Validation ===")

    # 1. List projects
    print("\n1. Listing projects...")
    projects = todoist_list_projects()
    print(f"   Found {len(projects)} projects")
    for p in projects[:5]:
        print(f"   - {p['name']} (id={p['id']})")

    # 2. List tasks
    print("\n2. Listing tasks...")
    tasks = todoist_list_tasks()
    print(f"   Found {len(tasks)} tasks")
    for t in tasks[:5]:
        due = t.get("due")
        if isinstance(due, dict):
            due_str = due.get("string", due.get("date", ""))
        elif due:
            due_str = str(due)
        else:
            due_str = "no due"
        print(f"   - {t['content']} (due: {due_str})")

    # 3. Create a task
    print("\n3. Creating test task...")
    new_task = todoist_create_task(
        "Phase 9 validation test task",
        due_string="tomorrow",
        priority=2,
    )
    task_id = new_task["id"]
    print(f"   Created: {new_task['content']} (id={task_id})")

    # 4. Complete the task
    print("\n4. Completing test task...")
    result = todoist_complete_task(task_id)
    print(f"   Status: {result['status']}")

    # 5. Verify it's gone from active tasks
    print("\n5. Verifying task is completed...")
    tasks_after = todoist_list_tasks()
    remaining_ids = [t["id"] for t in tasks_after]
    if task_id not in remaining_ids:
        print("   Task no longer in active list: PASS")
    else:
        print("   WARNING: Task still in active list")

    print("\n   Todoist: ALL PASS")


if __name__ == "__main__":
    try:
        validate_todoist()
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
