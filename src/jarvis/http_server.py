from __future__ import annotations

import asyncio
import uuid

import structlog
from aiohttp import web

from jarvis.channels.base import ChannelType

log = structlog.get_logger()


class InternalServer:
    """Lightweight HTTP bridge for Letta sandbox tools.

    Exposes endpoints that tools call to send messages and manage schedules.
    Uses AppRunner + TCPSite so it runs non-blocking alongside channels.
    """

    def __init__(self, router, scheduler, trigger, port: int = 9100) -> None:
        self._router = router
        self._scheduler = scheduler
        self._trigger = trigger
        self._port = port

    def _build_app(self) -> web.Application:
        """Build the aiohttp Application (separated for testability)."""
        app = web.Application()
        app.add_routes(
            [
                web.get("/health", self._health),
                web.post("/outbound", self._outbound),
                web.post("/scheduler/add", self._scheduler_add),
                web.post("/scheduler/remove", self._scheduler_remove),
                web.get("/scheduler/list", self._scheduler_list),
            ]
        )
        return app

    async def start(self) -> None:
        """Start the HTTP server and block forever."""
        app = self._build_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self._port)
        await site.start()
        log.info("http_server.started", port=self._port)
        await asyncio.Event().wait()

    async def _health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def _outbound(self, request: web.Request) -> web.Response:
        """Letta tool calls this to send a message to the user."""
        data = await request.json()
        channel_type = data["channel"]
        recipient_id = data["recipient_id"]
        text = data["text"]
        await self._router.send_proactive(
            ChannelType(channel_type), recipient_id, text
        )
        return web.json_response({"status": "sent"})

    async def _scheduler_add(self, request: web.Request) -> web.Response:
        """Add a reminder or cron job."""
        data = await request.json()
        job_type = data["type"]
        job_id = data.get("id", str(uuid.uuid4()))
        context = data["context"]
        notify_channel = data.get("notify_channel", "")
        notify_recipient = data.get("notify_recipient", "")

        if job_type == "reminder":
            delay = data["delay_seconds"]
            self._scheduler.add_reminder(
                job_id, delay, self._trigger.send,
                context, notify_channel, notify_recipient,
            )
        elif job_type == "cron":
            cron_expr = data["cron"]
            self._scheduler.add_cron(
                job_id, cron_expr, self._trigger.send,
                context, notify_channel, notify_recipient,
            )

        return web.json_response({"status": "added", "id": job_id})

    async def _scheduler_remove(self, request: web.Request) -> web.Response:
        """Remove a scheduled job by ID."""
        data = await request.json()
        removed = self._scheduler.remove_job(data["id"])
        status = "removed" if removed else "not_found"
        return web.json_response({"status": status})

    async def _scheduler_list(self, request: web.Request) -> web.Response:
        """List all scheduled jobs."""
        jobs = self._scheduler.list_jobs()
        return web.json_response({"jobs": jobs})
