from __future__ import annotations

import time
import uuid

import structlog
from aiohttp import web

from jarvis.monitoring.metrics import (
    ERROR_COUNT,
    HTTP_REQUEST_COUNT,
    HTTP_REQUEST_DURATION,
)

log = structlog.get_logger()


@web.middleware
async def observability_middleware(request: web.Request, handler):
    """Log requests, update Prometheus metrics, catch uncaught exceptions."""
    request_id = str(uuid.uuid4())[:8]
    start = time.monotonic()
    endpoint = request.path
    method = request.method

    try:
        response = await handler(request)
        duration = time.monotonic() - start
        status = str(response.status)

        HTTP_REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, status=status,
        ).inc()
        HTTP_REQUEST_DURATION.labels(
            method=method, endpoint=endpoint,
        ).observe(duration)

        log.debug(
            "http.request",
            request_id=request_id,
            method=method,
            path=endpoint,
            status=int(status),
            duration_ms=round(duration * 1000, 1),
        )
        return response

    except web.HTTPException:
        # Let aiohttp HTTP exceptions (404, 405, etc.) propagate normally
        raise

    except Exception as exc:
        duration = time.monotonic() - start

        HTTP_REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, status="500",
        ).inc()
        HTTP_REQUEST_DURATION.labels(
            method=method, endpoint=endpoint,
        ).observe(duration)
        ERROR_COUNT.labels(component="http").inc()

        log.error(
            "http.unhandled_error",
            request_id=request_id,
            method=method,
            path=endpoint,
            error=str(exc),
        )
        return web.json_response(
            {"error": "internal_server_error", "request_id": request_id},
            status=500,
        )
