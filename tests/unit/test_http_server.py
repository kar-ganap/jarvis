from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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

    # Mock Google handlers so tests don't call real APIs
    with patch("jarvis.http_server.google_handlers") as mock_google:
        mock_google.gmail_search.return_value = [
            {"id": "m1", "subject": "Test", "from": "a@b.com", "date": "2026-01-01"}
        ]
        mock_google.gmail_read.return_value = {
            "id": "m1", "subject": "Test", "from": "a@b.com",
            "to": "me@b.com", "date": "2026-01-01", "body": "hello",
        }
        mock_google.gmail_send.return_value = {"id": "sent-1", "thread_id": "t1"}
        mock_google.gmail_draft.return_value = {"id": "draft-1", "message_id": "md1"}
        mock_google.gcal_list_events.return_value = [
            {"id": "e1", "summary": "Standup", "start": "09:00", "end": "09:30", "location": ""}
        ]
        mock_google.gcal_create_event.return_value = {
            "id": "new-e", "html_link": "https://cal/new-e"
        }
        mock_google.gcal_update_event.return_value = {
            "id": "e1", "html_link": "https://cal/e1"
        }
        mock_google.gcal_delete_event.return_value = {"status": "deleted"}

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
        client._mock_google = mock_google
        yield client


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


class TestWhatsAppWebhook:
    async def test_whatsapp_inbound_dispatches(self, aiohttp_client):
        from jarvis.http_server import InternalServer

        mock_whatsapp = AsyncMock()
        with patch("jarvis.http_server.google_handlers"):
            server = InternalServer(
                router=AsyncMock(),
                scheduler=MagicMock(),
                trigger=AsyncMock(),
                whatsapp_channel=mock_whatsapp,
                port=0,
            )
            app = server._build_app()
            client = await aiohttp_client(app)

        resp = await client.post(
            "/whatsapp/inbound",
            json={
                "sender": "919876543210@s.whatsapp.net",
                "chat_jid": "919876543210@s.whatsapp.net",
                "push_name": "Kartik",
                "text": "hello",
                "is_group": False,
                "is_status": False,
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        mock_whatsapp.dispatch_webhook.assert_called_once()

    async def test_whatsapp_inbound_404_when_not_configured(self, aiohttp_client):
        from jarvis.http_server import InternalServer

        with patch("jarvis.http_server.google_handlers"):
            server = InternalServer(
                router=AsyncMock(),
                scheduler=MagicMock(),
                trigger=AsyncMock(),
                whatsapp_channel=None,
                port=0,
            )
            app = server._build_app()
            client = await aiohttp_client(app)

        resp = await client.post(
            "/whatsapp/inbound",
            json={"sender": "x", "text": "hi"},
        )
        assert resp.status == 404


class TestGoogleEndpoints:
    async def test_gmail_search_endpoint(self, test_client):
        resp = await test_client.post(
            "/google/gmail/search",
            json={"query": "from:alice", "max_results": 5},
        )
        assert resp.status == 200
        data = await resp.json()
        assert "results" in data

    async def test_gmail_send_endpoint(self, test_client):
        resp = await test_client.post(
            "/google/gmail/send",
            json={"to": "bob@example.com", "subject": "Hi", "body": "Hello"},
        )
        assert resp.status == 200
        data = await resp.json()
        assert "id" in data

    async def test_gcal_list_endpoint(self, test_client):
        resp = await test_client.post(
            "/google/gcal/list",
            json={"days_ahead": 1},
        )
        assert resp.status == 200
        data = await resp.json()
        assert "events" in data

    async def test_gcal_create_endpoint(self, test_client):
        resp = await test_client.post(
            "/google/gcal/create",
            json={
                "summary": "Lunch",
                "start_time": "2026-02-05T12:00:00Z",
                "end_time": "2026-02-05T13:00:00Z",
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert "id" in data
