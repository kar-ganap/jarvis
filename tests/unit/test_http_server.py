from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture()
async def test_client(aiohttp_client):
    """Create a test client for the internal HTTP server."""
    from jarvis.http_server import InternalServer

    mock_router = AsyncMock()
    mock_scheduler = MagicMock()
    mock_scheduler.list_jobs.return_value = []
    mock_scheduler.add_reminder.return_value = "test-job"
    mock_scheduler.add_cron.return_value = "test-cron"
    mock_scheduler.remove_job.return_value = True
    mock_trigger = AsyncMock()

    server = InternalServer(
        router=mock_router,
        scheduler=mock_scheduler,
        trigger=mock_trigger,
        port=0,
    )
    app = server._build_app()
    client = await aiohttp_client(app)
    client._mock_router = mock_router
    client._mock_scheduler = mock_scheduler
    return client


class TestHealthEndpoint:
    async def test_returns_ok(self, test_client):
        resp = await test_client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"


class TestOutboundEndpoint:
    async def test_calls_router_send_proactive(self, test_client):
        resp = await test_client.post(
            "/outbound",
            json={
                "channel": "slack",
                "recipient_id": "C123",
                "text": "Hello!",
            },
        )
        assert resp.status == 200
        test_client._mock_router.send_proactive.assert_called_once()


class TestSchedulerEndpoints:
    async def test_add_reminder(self, test_client):
        resp = await test_client.post(
            "/scheduler/add",
            json={
                "type": "reminder",
                "id": "rem-1",
                "context": "check PR",
                "delay_seconds": 300,
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "added"
        test_client._mock_scheduler.add_reminder.assert_called_once()

    async def test_add_cron(self, test_client):
        resp = await test_client.post(
            "/scheduler/add",
            json={
                "type": "cron",
                "id": "cron-1",
                "context": "morning briefing",
                "cron": "0 8 * * *",
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "added"
        test_client._mock_scheduler.add_cron.assert_called_once()

    async def test_remove(self, test_client):
        resp = await test_client.post(
            "/scheduler/remove",
            json={"id": "rem-1"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "removed"

    async def test_list(self, test_client):
        test_client._mock_scheduler.list_jobs.return_value = [
            {"id": "job-1", "next_run": "2026-01-01", "trigger": "date"}
        ]
        resp = await test_client.get("/scheduler/list")
        assert resp.status == 200
        data = await resp.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == "job-1"
