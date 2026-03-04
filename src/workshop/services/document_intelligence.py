"""Document Intelligence service — wraps the Azure DI SDK."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from azure.core.exceptions import HttpResponseError

from workshop.config import settings
from workshop.services.api_trace import ApiTrace, TraceTimer, sanitize_headers

logger = logging.getLogger(__name__)


def _get_client():  # type: ignore[no-untyped-def]
    """Lazy-initialize the DI client."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient

    if not settings.ai_services_endpoint:
        raise RuntimeError("AI_SERVICES_ENDPOINT not configured")

    credential = _get_credential()
    return DocumentIntelligenceClient(
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


def _make_request(file_bytes: bytes):  # type: ignore[no-untyped-def]
    """Build an AnalyzeDocumentRequest from raw bytes."""
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    return AnalyzeDocumentRequest(bytes_source=file_bytes)


async def analyze_layout(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Run DI Layout analysis on a document. Returns result + API trace."""
    client = _get_client()
    trace = ApiTrace(service="DI", operation="layout")
    trace.request_url = (
        f"{settings.ai_services_endpoint}"
        "documentintelligence/documentModels/prebuilt-layout:analyze"
    )
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/octet-stream"})

    with TraceTimer() as timer:
        try:

            def _run() -> Any:
                poller = client.begin_analyze_document(
                    model_id="prebuilt-layout",
                    body=_make_request(file_bytes),
                )
                return poller.result()

            result = await asyncio.to_thread(_run)
            trace.response_status = 200
            result_dict = _result_to_dict(result)
            trace.response_body = _summarize_result(result_dict)
        except HttpResponseError as e:
            trace.error = f"HttpResponseError: {e}"
            trace.response_status = e.status_code or 500
            result_dict = {}
        except Exception as e:
            trace.error = f"{type(e).__name__}: {e}"
            trace.response_status = 500
            result_dict = {}

    trace.duration_ms = timer.duration_ms
    return {"result": result_dict, "trace": trace.to_dict()}


async def analyze_prebuilt(model_id: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Run a DI prebuilt model (invoice, receipt, etc.). Returns result + API trace."""
    client = _get_client()
    trace = ApiTrace(service="DI", operation=model_id)
    trace.request_url = (
        f"{settings.ai_services_endpoint}documentintelligence/documentModels/{model_id}:analyze"
    )
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/octet-stream"})

    with TraceTimer() as timer:
        try:

            def _run() -> Any:
                poller = client.begin_analyze_document(
                    model_id=model_id,
                    body=_make_request(file_bytes),
                )
                return poller.result()

            result = await asyncio.to_thread(_run)
            trace.response_status = 200
            result_dict = _result_to_dict(result)
            trace.response_body = _summarize_result(result_dict)
        except HttpResponseError as e:
            trace.error = f"HttpResponseError: {e}"
            trace.response_status = e.status_code or 500
            result_dict = {}
        except Exception as e:
            trace.error = f"{type(e).__name__}: {e}"
            trace.response_status = 500
            result_dict = {}

    trace.duration_ms = timer.duration_ms
    return {"result": result_dict, "trace": trace.to_dict()}


def _result_to_dict(result: Any) -> dict[str, Any]:
    """Convert DI SDK result to a JSON-serializable dict."""
    try:
        if hasattr(result, "as_dict"):
            return result.as_dict()  # type: ignore[no-any-return]
        return json.loads(json.dumps(result, default=str))
    except Exception:
        return {"raw": str(result)}


def _summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    """Create a smaller summary for the API trace viewer (full result can be large)."""
    summary: dict[str, Any] = {}
    if "content" in result:
        content = result["content"]
        summary["content_preview"] = content[:500] + "..." if len(content) > 500 else content
    if "pages" in result:
        summary["page_count"] = len(result["pages"])
    if "tables" in result:
        summary["table_count"] = len(result["tables"])
    if "documents" in result:
        summary["document_count"] = len(result["documents"])
        if result["documents"]:
            doc = result["documents"][0]
            summary["doc_type"] = doc.get("docType", "unknown")
            summary["confidence"] = doc.get("confidence")
            summary["fields"] = {
                k: {
                    "value": str(v.get("content", v.get("value", "")))[:100],
                    "confidence": v.get("confidence"),
                }
                for k, v in (doc.get("fields") or {}).items()
            }
    return summary
