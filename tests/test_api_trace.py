"""API trace tests."""

from __future__ import annotations

from workshop.services.api_trace import ApiTrace, TraceTimer, sanitize_headers


def test_api_trace_to_dict():
    trace = ApiTrace(service="DI", operation="layout")
    trace.request_url = "https://example.com/api"
    trace.request_method = "POST"
    trace.response_status = 200
    trace.duration_ms = 123.456

    d = trace.to_dict()
    assert d["service"] == "DI"
    assert d["operation"] == "layout"
    assert d["request"]["url"] == "https://example.com/api"
    assert d["response"]["status"] == 200
    assert d["duration_ms"] == 123.46


def test_sanitize_headers():
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer secret123",
        "Ocp-Apim-Subscription-Key": "key456",
        "X-Custom": "visible",
    }
    sanitized = sanitize_headers(headers)
    assert sanitized["Content-Type"] == "application/json"
    assert sanitized["Authorization"] == "***REDACTED***"
    assert sanitized["Ocp-Apim-Subscription-Key"] == "***REDACTED***"
    assert sanitized["X-Custom"] == "visible"


def test_trace_timer():
    import time

    with TraceTimer() as t:
        time.sleep(0.01)
    assert t.duration_ms > 5  # At least 5ms
