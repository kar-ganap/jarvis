from __future__ import annotations


class TestPrometheusMetrics:
    def test_http_request_count_exists(self) -> None:
        """HTTP request counter is defined and incrementable."""
        from jarvis.monitoring.metrics import HTTP_REQUEST_COUNT

        before = HTTP_REQUEST_COUNT.labels(
            method="GET", endpoint="/health", status="200"
        )._value.get()
        HTTP_REQUEST_COUNT.labels(
            method="GET", endpoint="/health", status="200"
        ).inc()
        after = HTTP_REQUEST_COUNT.labels(
            method="GET", endpoint="/health", status="200"
        )._value.get()
        assert after == before + 1

    def test_http_request_duration_exists(self) -> None:
        """HTTP request duration histogram is defined and observable."""
        from jarvis.monitoring.metrics import HTTP_REQUEST_DURATION

        HTTP_REQUEST_DURATION.labels(
            method="GET", endpoint="/health"
        ).observe(0.123)

    def test_tool_invocation_count_exists(self) -> None:
        """Tool invocation counter is defined and incrementable."""
        from jarvis.monitoring.metrics import TOOL_INVOCATION_COUNT

        before = TOOL_INVOCATION_COUNT.labels(
            tool_name="browser_navigate"
        )._value.get()
        TOOL_INVOCATION_COUNT.labels(tool_name="browser_navigate").inc()
        after = TOOL_INVOCATION_COUNT.labels(
            tool_name="browser_navigate"
        )._value.get()
        assert after == before + 1

    def test_message_count_exists(self) -> None:
        """Message counter is defined with channel and direction labels."""
        from jarvis.monitoring.metrics import MESSAGE_COUNT

        before = MESSAGE_COUNT.labels(
            channel="slack", direction="inbound"
        )._value.get()
        MESSAGE_COUNT.labels(channel="slack", direction="inbound").inc()
        after = MESSAGE_COUNT.labels(
            channel="slack", direction="inbound"
        )._value.get()
        assert after == before + 1

    def test_error_count_exists(self) -> None:
        """Error counter is defined with component label."""
        from jarvis.monitoring.metrics import ERROR_COUNT

        before = ERROR_COUNT.labels(component="http")._value.get()
        ERROR_COUNT.labels(component="http").inc()
        after = ERROR_COUNT.labels(component="http")._value.get()
        assert after == before + 1
