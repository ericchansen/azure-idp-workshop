"""Batch processing — orchestrates CU enrichment + Search indexing for multiple documents."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from workshop.routers.documents import DocumentSource, read_sample
from workshop.services import ai_search as ais_service
from workshop.services import content_understanding as cu_service
from workshop.services.cu_fields import extract_field_value

# Default fields for batch enrichment
BATCH_FIELDS = [
    {"name": "summary", "type": "string", "description": "A 2-3 sentence summary of the document"},
    {"name": "key_topics", "type": "string", "description": "Main topics or themes"},
]


BatchItem = str | DocumentSource


async def process_batch(samples: list[str]) -> dict[str, Any]:
    """Process bundled samples through CU enrichment and Search indexing."""
    return await process_batch_items(samples)


async def process_batch_items(
    items: Sequence[BatchItem], upload_scope: str | None = None
) -> dict[str, Any]:
    """Process multiple documents: CU enrichment → Search indexing.

    Returns per-document results with timing and traces.
    """
    # Ensure index exists first
    ensure_result = await ais_service.ensure_index()
    ensure_status = ensure_result.get("trace", {}).get("response", {}).get("status", 0)
    if ensure_status >= 400 or ensure_result.get("trace", {}).get("error"):
        return {
            "result": {"documents": [], "summary": {"total": 0, "succeeded": 0, "failed": 0}},
            "error": ensure_result.get("trace", {}).get(
                "error", f"ensure_index returned HTTP {ensure_status}"
            ),
            "trace": {"ensure_index": ensure_result.get("trace", {})},
        }

    # Compute analyzer ID once (constant across all docs)
    field_sigs = sorted(f"{f['name']}:{f['type']}:{f['description']}" for f in BATCH_FIELDS)
    analyzer_id = "workshop_batch_" + hashlib.md5("|".join(field_sigs).encode()).hexdigest()[:12]

    results: list[dict[str, Any]] = []
    total_cu_ms = 0.0
    total_search_ms = 0.0
    succeeded = 0
    failed = 0

    for item in items:
        doc_result = await _process_single_item(item, analyzer_id, upload_scope)
        results.append(doc_result)

        if doc_result.get("error"):
            failed += 1
        else:
            succeeded += 1
            total_cu_ms += doc_result.get("cu_duration_ms", 0)
            total_search_ms += doc_result.get("search_duration_ms", 0)

    return {
        "result": {
            "documents": results,
            "summary": {
                "total": len(items),
                "succeeded": succeeded,
                "failed": failed,
                "total_cu_ms": round(total_cu_ms, 2),
                "total_search_ms": round(total_search_ms, 2),
                "total_ms": round(total_cu_ms + total_search_ms, 2),
            },
        },
        "trace": {
            "ensure_index": ensure_result.get("trace", {}),
        },
    }


async def _process_single(sample: str, analyzer_id: str) -> dict[str, Any]:
    """Process a single document: read → CU extract → index."""
    return await _process_single_item(sample, analyzer_id)


async def _process_single_item(
    item: BatchItem, analyzer_id: str, upload_scope: str | None = None
) -> dict[str, Any]:
    """Process a sample name or uploaded document source."""
    try:
        document = _resolve_batch_item(item)
    except Exception as e:
        return {"sample": _item_name(item), "error": f"Cannot read document: {e}"}

    # CU enrichment
    try:
        cu_result = await cu_service.analyze_custom(
            analyzer_id, document.content, document.filename, BATCH_FIELDS
        )
    except Exception as e:
        return {
            "sample": document.filename,
            "source_type": document.source_type,
            "error": f"CU extraction failed: {e}",
            "cu_trace": None,
        }

    cu_fields = cu_result.get("result", {}).get("fields", {})
    cu_duration = cu_result.get("trace", {}).get("duration_ms", 0)

    # Check for service-level failures (CU swallows errors into trace)
    cu_trace_status = cu_result.get("trace", {}).get("response", {}).get("status", 0)
    if cu_trace_status >= 400 or cu_result.get("trace", {}).get("error"):
        return {
            "sample": document.filename,
            "source_type": document.source_type,
            "error": cu_result.get("trace", {}).get("error", f"CU returned HTTP {cu_trace_status}"),
            "cu_duration_ms": round(cu_duration, 2),
            "cu_trace": cu_result.get("trace"),
        }

    # Build search document
    doc_id = ais_service.build_document_id(_search_id_source(document, upload_scope))

    search_doc = {
        "id": doc_id,
        "title": document.filename,
        "content": cu_result.get("result", {}).get("content", ""),
        "summary": extract_field_value(cu_fields, "summary"),
        "key_topics": extract_field_value(cu_fields, "key_topics"),
        "source_doc": document.filename,
        "source_type": document.source_type,
        "upload_scope": upload_scope if document.source_type == "upload" else "",
        "indexed_at": datetime.now(tz=UTC).isoformat(),
    }

    # Push to search index
    try:
        index_result = await ais_service.index_document(search_doc)
    except Exception as e:
        return {
            "sample": document.filename,
            "source_type": document.source_type,
            "error": f"Search indexing failed: {e}",
            "cu_fields": {
                f["name"]: extract_field_value(cu_fields, f["name"]) for f in BATCH_FIELDS
            },
            "cu_duration_ms": round(cu_duration, 2),
            "cu_trace": cu_result.get("trace"),
        }

    search_duration = index_result.get("trace", {}).get("duration_ms", 0)

    # Check for search-level failures
    search_trace_status = index_result.get("trace", {}).get("response", {}).get("status", 0)
    if search_trace_status >= 400 or index_result.get("trace", {}).get("error"):
        return {
            "sample": document.filename,
            "source_type": document.source_type,
            "error": index_result.get("trace", {}).get(
                "error", f"Search returned HTTP {search_trace_status}"
            ),
            "cu_fields": {
                f["name"]: extract_field_value(cu_fields, f["name"]) for f in BATCH_FIELDS
            },
            "cu_duration_ms": round(cu_duration, 2),
            "search_duration_ms": round(search_duration, 2),
            "cu_trace": cu_result.get("trace"),
            "search_trace": index_result.get("trace"),
        }

    return {
        "sample": document.filename,
        "source_type": document.source_type,
        "document_id": doc_id,
        "cu_fields": {f["name"]: extract_field_value(cu_fields, f["name"]) for f in BATCH_FIELDS},
        "cu_duration_ms": round(cu_duration, 2),
        "search_duration_ms": round(search_duration, 2),
        "cu_trace": cu_result.get("trace"),
        "search_trace": index_result.get("trace"),
    }


def _resolve_batch_item(item: BatchItem) -> DocumentSource:
    if isinstance(item, DocumentSource):
        return item
    return DocumentSource(
        content=read_sample(item),
        filename=item,
        id_source=item,
        source_type="sample",
    )


def _item_name(item: BatchItem) -> str:
    if isinstance(item, DocumentSource):
        return item.filename
    return item


def _search_id_source(document: DocumentSource, upload_scope: str | None) -> str:
    if document.source_type != "upload":
        return document.id_source
    return f"{document.id_source}:scope:{upload_scope}"
