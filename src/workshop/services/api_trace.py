"""API trace capture — records outgoing Azure SDK HTTP requests/responses."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ApiTrace:
    """Captured API request/response pair for the API viewer."""

    service: str  # "DI" or "CU"
    operation: str  # e.g. "layout", "prebuilt-invoice"
    request_url: str = ""
    request_method: str = ""
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: Any = None
    response_status: int = 0
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body: Any = None
    duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "operation": self.operation,
            "request": {
                "url": self.request_url,
                "method": self.request_method,
                "headers": self.request_headers,
                "body": self.request_body,
            },
            "response": {
                "status": self.response_status,
                "headers": self.response_headers,
                "body": self.response_body,
            },
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


# Sensitive headers to redact in traces
_REDACT_HEADERS = {"authorization", "ocp-apim-subscription-key", "api-key"}


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive values from headers."""
    return {
        k: ("***REDACTED***" if k.lower() in _REDACT_HEADERS else v) for k, v in headers.items()
    }


class TraceTimer:
    """Context manager for timing API calls."""

    def __init__(self) -> None:
        self.start: float = 0
        self.duration_ms: float = 0

    def __enter__(self) -> TraceTimer:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self.duration_ms = (time.perf_counter() - self.start) * 1000
