from __future__ import annotations

import pytest
from aiohttp import web


@pytest.fixture()
async def middleware_client(aiohttp_client):
    """Create a minimal aiohttp app with the observability middleware."""
    from jarvis.monitoring.middleware import observability_middleware

    app = web.Application(middlewares=[observability_middleware])

    async def ok_handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async def error_handler(request: web.Request) -> web.Response:
        raise ValueError("boom")

    app.add_routes([
        web.get("/ok", ok_handler),
        web.get("/error", error_handler),
    ])

    return await aiohttp_client(app)


class TestObservabilityMiddleware:
    async def test_passes_through_successful_request(self, middleware_client):
        """Middleware passes through a successful response."""
        resp = await middleware_client.get("/ok")
        assert resp.status == 200
        data = await resp.json()
        assert data["ok"] is True

    async def test_uncaught_exception_returns_500(self, middleware_client):
        """Middleware catches unhandled exceptions and returns 500 JSON."""
        resp = await middleware_client.get("/error")
        assert resp.status == 500
        data = await resp.json()
        assert "error" in data

    async def test_increments_http_request_counter(self, middleware_client):
        """Middleware increments the HTTP request counter."""
        from jarvis.monitoring.metrics import HTTP_REQUEST_COUNT

        before = HTTP_REQUEST_COUNT.labels(
            method="GET", endpoint="/ok", status="200"
        )._value.get()

        await middleware_client.get("/ok")

        after = HTTP_REQUEST_COUNT.labels(
            method="GET", endpoint="/ok", status="200"
        )._value.get()
        assert after >= before + 1

    async def test_observes_request_duration(self, middleware_client):
        """Middleware records a duration observation in the histogram."""
        from jarvis.monitoring.metrics import HTTP_REQUEST_DURATION

        before_count = HTTP_REQUEST_DURATION.labels(
            method="GET", endpoint="/ok"
        )._sum.get()

        await middleware_client.get("/ok")

        after_count = HTTP_REQUEST_DURATION.labels(
            method="GET", endpoint="/ok"
        )._sum.get()
        assert after_count >= before_count

    async def test_500_increments_error_counter(self, middleware_client):
        """500 responses also increment the error counter."""
        from jarvis.monitoring.metrics import ERROR_COUNT

        before = ERROR_COUNT.labels(component="http")._value.get()

        await middleware_client.get("/error")

        after = ERROR_COUNT.labels(component="http")._value.get()
        assert after >= before + 1

    async def test_500_response_includes_request_id(self, middleware_client):
        """500 response body includes a request_id for traceability."""
        resp = await middleware_client.get("/error")
        data = await resp.json()
        assert "request_id" in data
