"""Content Understanding service — wraps the Azure CU SDK."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from workshop.config import settings
from workshop.services.api_trace import ApiTrace, TraceTimer, sanitize_headers

logger = logging.getLogger(__name__)


def _get_client():  # type: ignore[no-untyped-def]
    """Lazy-initialize the CU client."""
    from azure.ai.contentunderstanding import ContentUnderstandingClient

    if not settings.ai_services_endpoint:
        raise RuntimeError("AI_SERVICES_ENDPOINT not configured")

    credential = _get_credential()
    return ContentUnderstandingClient(
        endpoint=settings.ai_services_endpoint,
        credential=credential,
    )


def _get_credential():  # type: ignore[no-untyped-def]
    """Return AzureKeyCredential if key set, else DefaultAzureCredential."""
    if settings.ai_services_key:
        from azure.core.credentials import AzureKeyCredential

        return AzureKeyCredential(settings.ai_services_key)
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def analyze_layout(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Run CU Layout analysis (prebuilt-layout analyzer). Returns result + API trace."""
    return _analyze_prebuilt("prebuilt-layout", file_bytes, filename)


def analyze_prebuilt(model_id: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Run a CU prebuilt analyzer (invoice, receipt, etc.). Returns result + API trace."""
    return _analyze_prebuilt(model_id, file_bytes, filename)


def analyze_custom(
    analyzer_id: str, file_bytes: bytes, filename: str, fields: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """Run a CU custom analyzer with optional field definitions. Returns result + API trace."""
    client = _get_client()
    trace = ApiTrace(service="CU", operation=f"custom/{analyzer_id}")
    trace.request_url = (
        f"{settings.ai_services_endpoint}contentunderstanding/analyzers/{analyzer_id}:analyze"
    )
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/octet-stream"})
    if fields:
        trace.request_body = {"fields": fields}

    with TraceTimer() as timer:
        try:
            _ensure_analyzer(client, analyzer_id, fields)

            poller = client.begin_analyze(
                analyzer_id=analyzer_id,
                analyze_request={"url": None},
                content_type="application/octet-stream",
                body=file_bytes,
            )
            result = poller.result()
            trace.response_status = 200
            result_dict = _result_to_dict(result)
            trace.response_body = result_dict
        except Exception as e:
            trace.error = str(e)
            trace.response_status = 500
            result_dict = {}

    trace.duration_ms = timer.duration_ms
    return {"result": result_dict, "trace": trace.to_dict()}


def _analyze_prebuilt(analyzer_id: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Internal: run a prebuilt CU analyzer."""
    client = _get_client()
    trace = ApiTrace(service="CU", operation=analyzer_id)
    trace.request_url = (
        f"{settings.ai_services_endpoint}contentunderstanding/analyzers/{analyzer_id}:analyze"
    )
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/octet-stream"})

    with TraceTimer() as timer:
        try:
            poller = client.begin_analyze(
                analyzer_id=analyzer_id,
                analyze_request={"url": None},
                content_type="application/octet-stream",
                body=file_bytes,
            )
            result = poller.result()
            trace.response_status = 200
            result_dict = _result_to_dict(result)
            trace.response_body = _summarize_cu_result(result_dict)
        except Exception as e:
            trace.error = str(e)
            trace.response_status = 500
            result_dict = {}

    trace.duration_ms = timer.duration_ms
    return {"result": result_dict, "trace": trace.to_dict()}


def _ensure_analyzer(client: Any, analyzer_id: str, fields: list[dict[str, str]] | None) -> None:
    """Create or update a custom analyzer if it doesn't exist."""
    try:
        client.get_analyzer(analyzer_id)
    except Exception:
        # Analyzer doesn't exist, create it
        analyzer_def: dict[str, Any] = {
            "description": f"Workshop custom analyzer: {analyzer_id}",
            "scenario": "document",
        }
        if fields:
            analyzer_def["fieldSchema"] = {
                "fields": {
                    f["name"]: {
                        "type": f.get("type", "string"),
                        "description": f.get("description", ""),
                    }
                    for f in fields
                }
            }
        client.begin_create_analyzer(analyzer_id=analyzer_id, body=analyzer_def).result()
        # Brief pause for analyzer to become available
        time.sleep(2)


def _result_to_dict(result: Any) -> dict[str, Any]:
    """Convert CU SDK result to JSON-serializable dict."""
    try:
        if hasattr(result, "as_dict"):
            return result.as_dict()  # type: ignore[no-any-return]
        if hasattr(result, "__dict__"):
            return json.loads(json.dumps(result.__dict__, default=str))
        return {"raw": str(result)}
    except Exception:
        return {"raw": str(result)}


def _summarize_cu_result(result: dict[str, Any]) -> dict[str, Any]:
    """Create a summary for the API trace viewer."""
    summary: dict[str, Any] = {}
    if "content" in result:
        content = result["content"]
        summary["content_preview"] = content[:500] + "..." if len(content) > 500 else content
    if "contents" in result:
        summary["content_count"] = len(result["contents"])
    if "fields" in result:
        summary["fields"] = {
            k: {
                "value": str(v.get("value", ""))[:200],
                "confidence": v.get("confidence"),
            }
            for k, v in result["fields"].items()
        }
    return summary
