"""Content Understanding service — wraps the Azure CU SDK."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from azure.core.exceptions import HttpResponseError

from workshop.config import settings
from workshop.services.api_trace import ApiTrace, TraceTimer, sanitize_headers

logger = logging.getLogger(__name__)

_defaults_configured = False


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


async def analyze_layout(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Run CU Layout analysis (prebuilt-layout analyzer). Returns result + API trace."""
    return await _analyze_prebuilt("prebuilt-layout", file_bytes, filename)


async def analyze_prebuilt(model_id: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Run a CU prebuilt analyzer (invoice, receipt, etc.). Returns result + API trace."""
    return await _analyze_prebuilt(model_id, file_bytes, filename)


async def analyze_custom(
    analyzer_id: str, file_bytes: bytes, filename: str, fields: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    """Run a CU custom analyzer with optional field definitions. Returns result + API trace."""
    client = _get_client()
    trace = ApiTrace(service="CU", operation=f"custom/{analyzer_id}")
    trace.request_url = (
        f"{settings.ai_services_endpoint}contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
    )
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/octet-stream"})
    if fields:
        trace.request_body = {"fields": fields}

    with TraceTimer() as timer:
        try:
            created = await asyncio.to_thread(_ensure_analyzer, client, analyzer_id, fields)
            if created:
                await asyncio.sleep(2)

            def _run_analysis() -> Any:
                poller = client.begin_analyze_binary(
                    analyzer_id=analyzer_id,
                    binary_input=file_bytes,
                    content_type="application/octet-stream",
                )
                return poller.result()

            result = await asyncio.to_thread(_run_analysis)
            trace.response_status = 200
            result_dict = _result_to_dict(result)
            trace.response_body = result_dict
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


async def _analyze_prebuilt(analyzer_id: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
    """Internal: run a prebuilt CU analyzer."""
    client = _get_client()
    trace = ApiTrace(service="CU", operation=analyzer_id)
    trace.request_url = (
        f"{settings.ai_services_endpoint}contentunderstanding/analyzers/{analyzer_id}:analyzeBinary"
    )
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/octet-stream"})

    with TraceTimer() as timer:
        try:

            def _run() -> Any:
                poller = client.begin_analyze_binary(
                    analyzer_id=analyzer_id,
                    binary_input=file_bytes,
                    content_type="application/octet-stream",
                )
                return poller.result()

            result = await asyncio.to_thread(_run)
            trace.response_status = 200
            result_dict = _result_to_dict(result)
            trace.response_body = _summarize_cu_result(result_dict)
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


def _ensure_defaults(client: Any) -> None:
    """Set CU resource-level model deployment defaults (once per process)."""
    global _defaults_configured  # noqa: PLW0603
    if _defaults_configured:
        return
    try:
        client.update_defaults(
            model_deployments={
                "gpt-4.1": settings.cu_completion_deployment,
                "text-embedding-3-large": settings.cu_embedding_deployment,
            }
        )
        _defaults_configured = True
        logger.info(
            "CU defaults configured: gpt-4.1→%s, text-embedding-3-large→%s",
            settings.cu_completion_deployment,
            settings.cu_embedding_deployment,
        )
    except Exception as e:
        logger.warning(
            "Failed to set CU defaults (gpt-4.1→%s): %s — "
            "CU custom analyzers may fail if deployment names don't match",
            settings.cu_completion_deployment,
            e,
        )


def _ensure_analyzer(client: Any, analyzer_id: str, fields: list[dict[str, str]] | None) -> bool:
    """Create a custom analyzer if it doesn't exist. Returns True if created."""
    _ensure_defaults(client)
    try:
        client.get_analyzer(analyzer_id)
        logger.debug("Analyzer '%s' already exists", analyzer_id)
        return False
    except Exception:
        logger.info("Analyzer '%s' not found — creating with completion model gpt-4.1", analyzer_id)
        analyzer_def: dict[str, Any] = {
            "description": f"Workshop custom analyzer: {analyzer_id}",
            "scenario": "document",
            "baseAnalyzerId": "prebuilt-document",
            "models": {"completion": "gpt-4.1"},
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
        try:
            client.begin_create_analyzer(
                analyzer_id=analyzer_id, resource=analyzer_def, allow_replace=True
            ).result()
            logger.info("Analyzer '%s' created successfully", analyzer_id)
            return True
        except Exception as e:
            logger.error("Failed to create analyzer '%s': %s", analyzer_id, e)
            raise RuntimeError(
                f"CU analyzer creation failed for '{analyzer_id}': {e}. "
                f"Check that GPT-4.1 deployment "
                f"'{settings.cu_completion_deployment}' exists."
            ) from e


def _result_to_dict(result: Any) -> dict[str, Any]:
    """Convert CU SDK result to JSON-serializable dict.

    CU returns results in a ``contents`` array. We also synthesize a top-level
    ``content`` string (aggregated markdown) so templates can use a consistent
    ``result.content`` path for both DI and CU.
    """
    try:
        if hasattr(result, "as_dict"):
            d: dict[str, Any] = result.as_dict()
        elif hasattr(result, "__dict__"):
            d = json.loads(json.dumps(result.__dict__, default=str))
        else:
            return {"raw": str(result)}

        # Synthesize top-level ``content`` from contents[].markdown
        if "contents" in d and "content" not in d:
            markdowns = [c.get("markdown", "") for c in d["contents"] if c.get("markdown")]
            if markdowns:
                d["content"] = "\n\n".join(markdowns)

        # Lift first content item's fields to top level for easy access
        if "contents" in d and "fields" not in d:
            for c in d["contents"]:
                if c.get("fields"):
                    d["fields"] = c["fields"]
                    break

        # Lift usage/token data to top level if present in contents
        if "usage" not in d:
            for c in d.get("contents", []):
                if c.get("usage"):
                    d["usage"] = c["usage"]
                    break

        return d
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
    if "usage" in result:
        summary["usage"] = result["usage"]
    return summary
