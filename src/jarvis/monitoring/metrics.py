from __future__ import annotations

from prometheus_client import Counter, Histogram, Info

APP_INFO = Info("jarvis", "Jarvis application metadata")

HTTP_REQUEST_COUNT = Counter(
    "jarvis_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "jarvis_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

TOOL_INVOCATION_COUNT = Counter(
    "jarvis_tool_invocations_total",
    "Total tool invocations",
    ["tool_name"],
)

MESSAGE_COUNT = Counter(
    "jarvis_messages_total",
    "Total messages processed",
    ["channel", "direction"],
)

ERROR_COUNT = Counter(
    "jarvis_errors_total",
    "Total errors",
    ["component"],
)
