from __future__ import annotations

from unittest.mock import MagicMock


class TestSchedulerEngine:
    def test_add_reminder(self):
        from jarvis.scheduler.engine import SchedulerEngine

        engine = SchedulerEngine()
        engine.start()

        callback = MagicMock()
        job_id = engine.add_reminder("test-reminder", 60, callback, "hello")

        assert job_id == "test-reminder"
        jobs = engine.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["id"] == "test-reminder"

        engine.shutdown()

    def test_add_cron(self):
        from jarvis.scheduler.engine import SchedulerEngine

        engine = SchedulerEngine()
        engine.start()

        callback = MagicMock()
        job_id = engine.add_cron("daily-8am", "0 8 * * *", callback, "briefing")

        assert job_id == "daily-8am"
        jobs = engine.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["id"] == "daily-8am"

        engine.shutdown()

    def test_remove_job(self):
        from jarvis.scheduler.engine import SchedulerEngine

        engine = SchedulerEngine()
        engine.start()

        callback = MagicMock()
        engine.add_reminder("to-remove", 60, callback, "bye")

        assert engine.remove_job("to-remove") is True
        assert engine.list_jobs() == []

        engine.shutdown()

    def test_remove_nonexistent(self):
        from jarvis.scheduler.engine import SchedulerEngine

        engine = SchedulerEngine()
        engine.start()

        assert engine.remove_job("no-such-job") is False

        engine.shutdown()

    def test_list_jobs_empty(self):
        from jarvis.scheduler.engine import SchedulerEngine

        engine = SchedulerEngine()
        engine.start()

        assert engine.list_jobs() == []

        engine.shutdown()
