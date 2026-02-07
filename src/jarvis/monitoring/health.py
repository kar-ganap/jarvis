from __future__ import annotations

import asyncio
import time

_start_time: float | None = None


def mark_started() -> None:
    """Record the application start time."""
    global _start_time
    _start_time = time.monotonic()


def get_uptime_seconds() -> float:
    """Return seconds since mark_started(), or 0.0 if not called."""
    if _start_time is None:
        return 0.0
    return time.monotonic() - _start_time


async def check_letta(client, agent_id: str) -> dict:
    """Check Letta agent connectivity.

    Returns a dict with name, ok, and optional error.
    """
    try:
        await asyncio.to_thread(client.agents.retrieve, agent_id=agent_id)
        return {"name": "letta", "ok": True}
    except Exception as exc:
        return {"name": "letta", "ok": False, "error": str(exc)}


def build_report(
    checks: list[dict],
    tool_count: int,
    channels: list[str],
) -> dict:
    """Aggregate health checks into a report dict."""
    all_ok = all(c["ok"] for c in checks)
    status = "ok" if all_ok else "unhealthy"
    return {
        "status": status,
        "uptime_seconds": round(get_uptime_seconds(), 2),
        "checks": checks,
        "tool_count": tool_count,
        "channels": channels,
    }
