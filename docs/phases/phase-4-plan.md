# Phase 4 Plan: Scheduler + Proactive Messaging

## Goal

Make Jarvis proactive. Add a scheduler for reminders and recurring jobs, an internal HTTP bridge so Letta sandbox tools can reach the app's router and scheduler, and tools for the agent to send messages and manage schedules.

---

## File-by-File Breakdown

### 1. `src/jarvis/scheduler/__init__.py` — empty

### 2. `src/jarvis/scheduler/engine.py` — APScheduler wrapper

Thin wrapper around APScheduler's `AsyncIOScheduler` with a clean API.

```python
class SchedulerEngine:
    def __init__(self):
        self._scheduler = AsyncIOScheduler()

    def start(self) -> None:
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def add_reminder(self, job_id: str, delay_seconds: int,
                     callback, *args) -> str:
        """One-shot job that fires after delay_seconds."""
        run_at = datetime.now() + timedelta(seconds=delay_seconds)
        self._scheduler.add_job(
            callback, 'date', run_date=run_at,
            id=job_id, args=args,
        )
        return job_id

    def add_cron(self, job_id: str, cron_expr: str,
                 callback, *args) -> str:
        """Recurring job from cron expression (e.g., '0 8 * * *')."""
        trigger = CronTrigger.from_crontab(cron_expr)
        self._scheduler.add_job(
            callback, trigger, id=job_id, args=args,
        )
        return job_id

    def remove_job(self, job_id: str) -> bool:
        try:
            self._scheduler.remove_job(job_id)
            return True
        except JobLookupError:
            return False

    def list_jobs(self) -> list[dict]:
        return [
            {"id": j.id, "next_run": str(j.next_run_time), "trigger": str(j.trigger)}
            for j in self._scheduler.get_jobs()
        ]
```

Key decisions:
- `CronTrigger.from_crontab()` parses standard 5-field cron expressions
- `add_reminder` uses `date` trigger with a computed `run_date`
- `list_jobs` returns plain dicts — serializable for HTTP and tool responses
- Custom `job_id` strings for deterministic identification

### 3. `src/jarvis/scheduler/triggers.py` — AgentTrigger

When a scheduled job fires, it sends a message to the Letta agent.

```python
class AgentTrigger:
    def __init__(self, client, agent_id: str):
        self._client = client
        self._agent_id = agent_id

    async def send(self, context: str) -> None:
        """Send a [scheduler|system] message to the agent."""
        prefixed = f"[scheduler|system] {context}"
        await asyncio.to_thread(
            self._client.agents.messages.create,
            agent_id=self._agent_id,
            messages=[{"role": "user", "content": prefixed}],
        )
```

The trigger doesn't decide whether to notify the user — the agent does. The agent receives the scheduler message, reasons about it, and may call `send_message_to_user` if it decides a notification is warranted.

### 4. `src/jarvis/http_server.py` — Internal HTTP bridge

Lightweight aiohttp server using `AppRunner` + `TCPSite` (non-blocking, runs alongside channels).

```python
class InternalServer:
    def __init__(self, router, scheduler, trigger, port=9100):
        self._router = router
        self._scheduler = scheduler
        self._trigger = trigger
        self._port = port

    async def start(self) -> None:
        app = web.Application()
        app.add_routes([
            web.get('/health', self._health),
            web.post('/outbound', self._outbound),
            web.post('/scheduler/add', self._scheduler_add),
            web.post('/scheduler/remove', self._scheduler_remove),
            web.get('/scheduler/list', self._scheduler_list),
        ])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self._port)
        await site.start()
        # Keep running forever
        await asyncio.Event().wait()

    async def _health(self, request):
        return web.json_response({"status": "ok"})

    async def _outbound(self, request):
        """Letta tool calls this to send a message to the user."""
        data = await request.json()
        channel_type = data["channel"]
        recipient_id = data["recipient_id"]
        text = data["text"]
        await self._router.send_proactive(
            ChannelType(channel_type), recipient_id, text
        )
        return web.json_response({"status": "sent"})

    async def _scheduler_add(self, request):
        """Add a reminder or cron job."""
        data = await request.json()
        job_type = data["type"]  # "reminder" or "cron"
        job_id = data.get("id", str(uuid.uuid4()))
        context = data["context"]

        if job_type == "reminder":
            delay = data["delay_seconds"]
            self._scheduler.add_reminder(
                job_id, delay, self._trigger.send, context
            )
        elif job_type == "cron":
            cron_expr = data["cron"]
            self._scheduler.add_cron(
                job_id, cron_expr, self._trigger.send, context
            )
        return web.json_response({"status": "added", "id": job_id})

    async def _scheduler_remove(self, request):
        data = await request.json()
        removed = self._scheduler.remove_job(data["id"])
        return web.json_response({"status": "removed" if removed else "not_found"})

    async def _scheduler_list(self, request):
        jobs = self._scheduler.list_jobs()
        return web.json_response({"jobs": jobs})
```

Key decisions:
- **`0.0.0.0`**: Listens on all interfaces so Docker containers (Letta) can reach it
- **`asyncio.Event().wait()`**: Keeps the server task alive in `asyncio.gather`
- **`_outbound`**: Bridges Letta sandbox → router → channel. Tool calls `POST /outbound` with channel/recipient/text.
- **`_scheduler_add`**: Bridges Letta sandbox → scheduler. Creates reminder or cron, wiring `trigger.send` as callback.

### 5. `src/jarvis/tools/messaging.py` — Proactive messaging tool

```python
def send_message_to_user(channel: str, recipient_id: str, text: str) -> str:
    """Send a message to the user on a specific channel.

    Args:
        channel: The channel to send on ('cli' or 'slack').
        recipient_id: The recipient identifier (channel ID for Slack).
        text: The message text to send.

    Returns:
        Confirmation or error message.
    """
    import os
    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    url = f"http://{host}:{port}/outbound"

    resp = requests.post(url, json={
        "channel": channel,
        "recipient_id": recipient_id,
        "text": text,
    }, timeout=10)
    resp.raise_for_status()
    return f"OK: Message sent to {channel}"

TOOLS = [send_message_to_user]
```

### 6. `src/jarvis/tools/scheduler_tool.py` — Scheduler tools

```python
def create_reminder(text: str, delay_minutes: int) -> str:
    """Create a one-time reminder that fires after the specified delay.

    Args:
        text: The reminder text / context.
        delay_minutes: Minutes until the reminder fires.

    Returns:
        Confirmation with the job ID.
    """
    import os
    import uuid
    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    job_id = f"reminder-{uuid.uuid4().hex[:8]}"
    resp = requests.post(f"http://{host}:{port}/scheduler/add", json={
        "type": "reminder",
        "id": job_id,
        "context": text,
        "delay_seconds": delay_minutes * 60,
    }, timeout=10)
    resp.raise_for_status()
    return f"OK: Reminder '{text}' set for {delay_minutes} minutes (id: {job_id})"


def create_recurring_job(text: str, cron_expression: str) -> str:
    """Create a recurring scheduled job using a cron expression.

    Args:
        text: Description/context sent to the agent on each trigger.
        cron_expression: Standard 5-field cron (e.g., '0 8 * * *' for 8am daily).

    Returns:
        Confirmation with the job ID.
    """
    import os
    import uuid
    import requests

    port = os.environ.get("JARVIS_HTTP_PORT", "9100")
    host = os.environ.get("JARVIS_HTTP_HOST", "host.docker.internal")
    job_id = f"cron-{uuid.uuid4().hex[:8]}"
    resp = requests.post(f"http://{host}:{port}/scheduler/add", json={
        "type": "cron",
        "id": job_id,
        "context": text,
        "cron": cron_expression,
    }, timeout=10)
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
    resp = requests.get(f"http://{host}:{port}/scheduler/list", timeout=10)
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
    resp = requests.post(f"http://{host}:{port}/scheduler/remove", json={
        "id": job_id,
    }, timeout=10)
    resp.raise_for_status()
    status = resp.json().get("status", "unknown")
    if status == "removed":
        return f"OK: Job '{job_id}' removed."
    return f"Job '{job_id}' not found."


TOOLS = [create_reminder, create_recurring_job, list_scheduled_jobs, remove_scheduled_job]
```

### 7. Update `src/jarvis/settings.py` — Add HttpSettings

```python
class HttpSettings(BaseModel):
    port: int = 9100
    host: str = "0.0.0.0"
```

### 8. Update `src/jarvis/app.py` — Wire everything together

```python
async def start(self) -> None:
    client = Letta(...)
    agent = get_or_create_agent(client, self.settings)
    channels = ChannelRegistry.build(self.settings)
    router = MessageRouter(client=client, agent_id=agent.id, channels=channels)

    # Scheduler + trigger
    scheduler = SchedulerEngine()
    scheduler.start()
    trigger = AgentTrigger(client=client, agent_id=agent.id)

    # Internal HTTP server
    http_server = InternalServer(
        router=router, scheduler=scheduler, trigger=trigger,
        port=self.settings.http.port,
    )

    # Start all concurrently
    tasks = [
        asyncio.create_task(http_server.start()),
        *[asyncio.create_task(ch.start(on_message=router.handle_inbound))
          for ch in channels.values()],
    ]
    await asyncio.gather(*tasks)
```

### 9. Update `src/jarvis/agent/factory.py` — Register new tools

Add `messaging` and `scheduler_tool` to `collect_tools(...)`.

### 10. Update `config/jarvis.yaml` and `.env`

```yaml
http:
  port: 9100
  host: "0.0.0.0"
```

Add to `.env` (for Letta sandbox):
```
JARVIS_HTTP_HOST=host.docker.internal
JARVIS_HTTP_PORT=9100
```

---

## Test Plan

### Unit Tests (Mock) — `tests/unit/`

#### `tests/unit/test_scheduler_engine.py`

1. **test_add_reminder** — Adds a one-shot job, appears in list_jobs
2. **test_add_cron** — Adds a cron job, appears in list_jobs
3. **test_remove_job** — Removes a job, no longer in list
4. **test_remove_nonexistent** — Returns False for unknown job ID
5. **test_list_jobs_empty** — Empty scheduler returns empty list

#### `tests/unit/test_trigger.py`

1. **test_send_formats_message** — Sends `[scheduler|system] <context>` to Letta
2. **test_send_uses_correct_agent** — Message sent to the right agent ID

#### `tests/unit/test_http_server.py`

1. **test_health_endpoint** — GET /health returns 200 + {"status": "ok"}
2. **test_outbound_endpoint** — POST /outbound calls router.send_proactive
3. **test_scheduler_add_reminder** — POST /scheduler/add with type=reminder adds job
4. **test_scheduler_add_cron** — POST /scheduler/add with type=cron adds job
5. **test_scheduler_remove** — POST /scheduler/remove removes job
6. **test_scheduler_list** — GET /scheduler/list returns jobs

#### `tests/unit/test_messaging_tool.py`

1. **test_send_message_posts_to_bridge** — Calls HTTP bridge with correct payload
2. **test_send_message_missing_host** — Returns error when bridge unreachable

#### `tests/unit/test_scheduler_tool.py`

1. **test_create_reminder_posts_to_bridge** — Calls HTTP bridge with reminder payload
2. **test_create_recurring_posts_to_bridge** — Calls HTTP bridge with cron payload
3. **test_list_jobs_returns_formatted** — Formats job list from bridge response
4. **test_remove_job_posts_to_bridge** — Calls HTTP bridge with remove payload

### Integration Tests (Real Letta) — `tests/integration/`

#### `tests/integration/test_scheduler_roundtrip.py`

1. **test_reminder_fires** — Create a 3-second reminder via HTTP bridge, verify trigger.send is called

---

## Acceptance Criteria (Validation Gate)

Phase 4 is **complete** when:

1. `uv run pytest tests/unit/ -v` — all unit tests pass
2. `uv run pytest tests/integration/ -v` — all integration tests pass
3. `uv run ruff check src/ tests/` — no lint errors
4. On Slack: "remind me in 1 minute to check the PR" → 1 minute later, Jarvis sends a notification
5. On Slack: "what reminders do I have?" → Jarvis lists active jobs

---

## Dependencies

```bash
uv add apscheduler    # Already added
```

Add to `.env`:
```
JARVIS_HTTP_HOST=host.docker.internal
JARVIS_HTTP_PORT=9100
```
