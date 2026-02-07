from __future__ import annotations

import asyncio
import uuid

import structlog
from aiohttp import web

from jarvis.browser import handlers as browser_handlers
from jarvis.channels.base import ChannelType
from jarvis.google import handlers as google_handlers
from jarvis.google import slides_handlers
from jarvis.notion import handlers as notion_handlers

log = structlog.get_logger()


class InternalServer:
    """Lightweight HTTP bridge for Letta sandbox tools.

    Exposes endpoints that tools call to send messages and manage schedules.
    Uses AppRunner + TCPSite so it runs non-blocking alongside channels.
    """

    def __init__(
        self, router, scheduler, trigger, whatsapp_channel=None, port: int = 9100,
    ) -> None:
        self._router = router
        self._scheduler = scheduler
        self._trigger = trigger
        self._whatsapp_channel = whatsapp_channel
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
                # WhatsApp webhook
                web.post("/whatsapp/inbound", self._whatsapp_inbound),
                # Google API bridge
                web.post("/google/gmail/search", self._gmail_search),
                web.post("/google/gmail/read", self._gmail_read),
                web.post("/google/gmail/send", self._gmail_send),
                web.post("/google/gmail/draft", self._gmail_draft),
                web.post("/google/gcal/list", self._gcal_list),
                web.post("/google/gcal/create", self._gcal_create),
                web.post("/google/gcal/update", self._gcal_update),
                web.post("/google/gcal/delete", self._gcal_delete),
                # Notion
                web.post("/notion/search", self._notion_search),
                web.post("/notion/read", self._notion_read),
                web.post("/notion/create", self._notion_create),
                web.post("/notion/append", self._notion_append),
                web.post("/notion/query_db", self._notion_query_db),
                # Google Slides
                web.post("/google/slides/list", self._gslides_list),
                web.post("/google/slides/read", self._gslides_read),
                web.post("/google/slides/create", self._gslides_create),
                web.post("/google/slides/add_slide", self._gslides_add_slide),
                # Browser
                web.post("/browser/navigate", self._browser_navigate),
                web.post("/browser/screenshot", self._browser_screenshot),
                web.post("/browser/extract", self._browser_extract),
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

    # --- WhatsApp webhook ---

    async def _whatsapp_inbound(self, request: web.Request) -> web.Response:
        """Receive inbound WhatsApp message from the Baileys bridge."""
        if not self._whatsapp_channel:
            return web.json_response({"error": "whatsapp not configured"}, status=404)
        data = await request.json()
        await self._whatsapp_channel.dispatch_webhook(data)
        return web.json_response({"status": "ok"})

    # --- Google API bridge handlers ---

    async def _gmail_search(self, request: web.Request) -> web.Response:
        data = await request.json()
        results = await asyncio.to_thread(
            google_handlers.gmail_search, data["query"], data.get("max_results", 5)
        )
        return web.json_response({"results": results})

    async def _gmail_read(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(google_handlers.gmail_read, data["message_id"])
        return web.json_response(result)

    async def _gmail_send(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            google_handlers.gmail_send, data["to"], data["subject"], data["body"]
        )
        return web.json_response(result)

    async def _gmail_draft(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            google_handlers.gmail_draft, data["to"], data["subject"], data["body"]
        )
        return web.json_response(result)

    async def _gcal_list(self, request: web.Request) -> web.Response:
        data = await request.json()
        events = await asyncio.to_thread(
            google_handlers.gcal_list_events, data.get("days_ahead", 1)
        )
        return web.json_response({"events": events})

    async def _gcal_create(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            google_handlers.gcal_create_event,
            data["summary"], data["start_time"], data["end_time"],
            data.get("description", ""), data.get("location", ""),
        )
        return web.json_response(result)

    async def _gcal_update(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            google_handlers.gcal_update_event,
            data["event_id"],
            data.get("summary", ""), data.get("start_time", ""),
            data.get("end_time", ""), data.get("description", ""),
            data.get("location", ""),
        )
        return web.json_response(result)

    async def _gcal_delete(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            google_handlers.gcal_delete_event, data["event_id"]
        )
        return web.json_response(result)

    # --- Notion bridge handlers ---

    async def _notion_search(self, request: web.Request) -> web.Response:
        data = await request.json()
        results = await asyncio.to_thread(
            notion_handlers.notion_search,
            data["query"], data.get("max_results", 10),
        )
        return web.json_response({"results": results})

    async def _notion_read(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            notion_handlers.notion_read_page, data["page_id"],
        )
        return web.json_response(result)

    async def _notion_create(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            notion_handlers.notion_create_page,
            data["parent_id"], data["title"], data.get("content", ""),
        )
        return web.json_response(result)

    async def _notion_append(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            notion_handlers.notion_append_blocks,
            data["page_id"], data["content"],
        )
        return web.json_response(result)

    async def _notion_query_db(self, request: web.Request) -> web.Response:
        data = await request.json()
        results = await asyncio.to_thread(
            notion_handlers.notion_query_database,
            data["database_id"], data.get("filter_json", ""),
        )
        return web.json_response({"results": results})

    # --- Google Slides bridge handlers ---

    async def _gslides_list(self, request: web.Request) -> web.Response:
        data = await request.json()
        results = await asyncio.to_thread(
            slides_handlers.gslides_list, data.get("max_results", 10)
        )
        return web.json_response({"results": results})

    async def _gslides_read(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            slides_handlers.gslides_read, data["presentation_id"]
        )
        return web.json_response(result)

    async def _gslides_create(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            slides_handlers.gslides_create, data["title"]
        )
        return web.json_response(result)

    async def _gslides_add_slide(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            slides_handlers.gslides_add_slide,
            data["presentation_id"], data["title"], data["body"],
        )
        return web.json_response(result)

    # --- Browser bridge handlers ---

    async def _browser_navigate(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            browser_handlers.browser_navigate, data["url"]
        )
        return web.json_response(result)

    async def _browser_screenshot(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            browser_handlers.browser_screenshot, data["url"]
        )
        return web.json_response(result)

    async def _browser_extract(self, request: web.Request) -> web.Response:
        data = await request.json()
        result = await asyncio.to_thread(
            browser_handlers.browser_extract, data["url"], data["selector"],
        )
        return web.json_response(result)
