from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestTodoistListTasks:
    def test_returns_tasks(self):
        from jarvis.todoist.handlers import todoist_list_tasks

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "id": "task-1",
                "content": "Buy groceries",
                "due": {"string": "today"},
                "priority": 1,
                "project_id": "proj-1",
            },
            {
                "id": "task-2",
                "content": "Call dentist",
                "due": None,
                "priority": 3,
                "project_id": "proj-1",
            },
        ]
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.get", return_value=mock_resp) as mock_get, \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            results = todoist_list_tasks()

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["id"] == "task-1"
        assert results[0]["content"] == "Buy groceries"
        mock_get.assert_called_once()

    def test_empty_results(self):
        from jarvis.todoist.handlers import todoist_list_tasks

        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.get", return_value=mock_resp), \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            results = todoist_list_tasks()

        assert results == []

    def test_missing_api_key(self):
        import pytest

        from jarvis.todoist.handlers import todoist_list_tasks

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TODOIST_API_KEY"):
                todoist_list_tasks()

    def test_filter_by_project(self):
        from jarvis.todoist.handlers import todoist_list_tasks

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "id": "task-1", "content": "Task in project",
                "due": None, "priority": 1, "project_id": "proj-42",
            },
        ]
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.get", return_value=mock_resp) as mock_get, \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            results = todoist_list_tasks(project_id="proj-42")

        assert len(results) == 1
        # Verify project_id was passed as query param
        call_kwargs = mock_get.call_args
        assert "proj-42" in str(call_kwargs)


class TestTodoistCreateTask:
    def test_creates_task(self):
        from jarvis.todoist.handlers import todoist_create_task

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "id": "new-task-1",
            "content": "Write report",
            "due": {"string": "tomorrow"},
            "priority": 2,
            "url": "https://todoist.com/task/new-task-1",
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.post", return_value=mock_resp) as mock_post, \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            result = todoist_create_task("Write report", due_string="tomorrow", priority=2)

        assert result["id"] == "new-task-1"
        assert result["content"] == "Write report"
        mock_post.assert_called_once()


class TestTodoistCompleteTask:
    def test_completes_task(self):
        from jarvis.todoist.handlers import todoist_complete_task

        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.post", return_value=mock_resp), \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            result = todoist_complete_task("task-1")

        assert result["status"] == "completed"


class TestTodoistListProjects:
    def test_returns_projects(self):
        from jarvis.todoist.handlers import todoist_list_projects

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"id": "proj-1", "name": "Inbox", "color": "grey"},
            {"id": "proj-2", "name": "Work", "color": "blue"},
        ]
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.get", return_value=mock_resp), \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            results = todoist_list_projects()

        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["id"] == "proj-1"
        assert results[0]["name"] == "Inbox"

    def test_empty_projects(self):
        from jarvis.todoist.handlers import todoist_list_projects

        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()

        with patch("jarvis.todoist.handlers.requests.get", return_value=mock_resp), \
             patch.dict("os.environ", {"TODOIST_API_KEY": "test-key"}):
            results = todoist_list_projects()

        assert results == []
