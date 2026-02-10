from __future__ import annotations

from unittest.mock import MagicMock


class TestMarkStarted:
    def test_uptime_increases_after_mark(self) -> None:
        """get_uptime_seconds returns positive value after mark_started."""
        import time

        from jarvis.monitoring.health import get_uptime_seconds, mark_started

        mark_started()
        time.sleep(0.01)
        assert get_uptime_seconds() > 0

    def test_uptime_zero_before_mark(self) -> None:
        """get_uptime_seconds returns 0.0 if mark_started was never called."""
        from jarvis.monitoring import health

        health._start_time = None
        assert health.get_uptime_seconds() == 0.0


class TestCheckLetta:
    async def test_returns_ok_when_reachable(self) -> None:
        """check_letta returns ok=True when agent is accessible."""
        from jarvis.monitoring.health import check_letta

        mock_client = MagicMock()
        mock_agent = MagicMock()
        mock_agent.name = "jarvis"
        mock_client.agents.retrieve.return_value = mock_agent

        result = await check_letta(mock_client, "agent-123")
        assert result["name"] == "letta"
        assert result["ok"] is True

    async def test_returns_fail_when_unreachable(self) -> None:
        """check_letta returns ok=False when agent retrieval raises."""
        from jarvis.monitoring.health import check_letta

        mock_client = MagicMock()
        mock_client.agents.retrieve.side_effect = ConnectionError("nope")

        result = await check_letta(mock_client, "agent-123")
        assert result["name"] == "letta"
        assert result["ok"] is False
        assert "nope" in result["error"]


class TestBuildReport:
    def test_all_checks_ok_returns_ok(self) -> None:
        """build_report returns status=ok when all checks pass."""
        from jarvis.monitoring.health import build_report

        checks = [{"name": "letta", "ok": True}]
        report = build_report(checks, tool_count=30, channels=["cli", "slack"])
        assert report["status"] == "ok"
        assert report["tool_count"] == 30
        assert report["channels"] == ["cli", "slack"]
        assert "uptime_seconds" in report

    def test_failing_check_returns_unhealthy(self) -> None:
        """build_report returns status=unhealthy when a check fails."""
        from jarvis.monitoring.health import build_report

        checks = [{"name": "letta", "ok": False, "error": "unreachable"}]
        report = build_report(checks, tool_count=30, channels=["cli"])
        assert report["status"] == "unhealthy"

    def test_to_dict_is_serializable(self) -> None:
        """build_report output is JSON-serializable."""
        import json

        from jarvis.monitoring.health import build_report

        report = build_report(
            [{"name": "letta", "ok": True}], tool_count=10, channels=["cli"]
        )
        serialized = json.dumps(report)
        assert isinstance(serialized, str)

    def test_report_includes_uptime(self) -> None:
        """build_report includes uptime_seconds from get_uptime_seconds."""
        import time

        from jarvis.monitoring.health import build_report, mark_started

        mark_started()
        time.sleep(0.01)
        report = build_report(
            [{"name": "letta", "ok": True}], tool_count=5, channels=[]
        )
        assert report["uptime_seconds"] > 0
