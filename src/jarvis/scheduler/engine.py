from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class SchedulerEngine:
    """Thin wrapper around APScheduler's BackgroundScheduler.

    Uses BackgroundScheduler (thread-based) so it works without a running
    event loop.  Async callbacks are dispatched to the event loop captured
    during ``start()``.
    """

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self) -> None:
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def _invoke(self, callback, *args) -> None:
        """Call *callback*, scheduling on the event loop if it is async."""
        if asyncio.iscoroutinefunction(callback) and self._loop:
            asyncio.run_coroutine_threadsafe(callback(*args), self._loop)
        else:
            callback(*args)

    def add_reminder(
        self, job_id: str, delay_seconds: int, callback, *args
    ) -> str:
        """One-shot job that fires after delay_seconds."""
        run_at = datetime.now() + timedelta(seconds=delay_seconds)
        self._scheduler.add_job(
            self._invoke,
            "date",
            run_date=run_at,
            id=job_id,
            args=(callback, *args),
        )
        return job_id

    def add_cron(
        self, job_id: str, cron_expr: str, callback, *args
    ) -> str:
        """Recurring job from cron expression (e.g., '0 8 * * *')."""
        trigger = CronTrigger.from_crontab(cron_expr)
        self._scheduler.add_job(
            self._invoke, trigger, id=job_id, args=(callback, *args)
        )
        return job_id

    def remove_job(self, job_id: str) -> bool:
        try:
            self._scheduler.remove_job(job_id)
        except JobLookupError:
            return False
        return True

    def list_jobs(self) -> list[dict]:
        return [
            {
                "id": j.id,
                "next_run": str(j.next_run_time),
                "trigger": str(j.trigger),
            }
            for j in self._scheduler.get_jobs()
        ]
