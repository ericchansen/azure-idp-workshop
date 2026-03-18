"""Batch processing — orchestrates CU enrichment + Search indexing for multiple documents."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from workshop.routers.documents import read_sample
from workshop.services import ai_search as ais_service
from workshop.services import content_understanding as cu_service

logger = logging.getLogger(__name__)

# Default fields for batch enrichment
BATCH_FIELDS = [
    {"name": "summary", "type": "string", "description": "A 2-3 sentence summary of the document"},
    {"name": "key_topics", "type": "string", "description": "Main topics or themes"},
]


async def process_batch(samples: list[str]) -> dict[str, Any]:
    """Process multiple documents: CU enrichment → Search indexing.

    Returns per-document results with timing and traces.
    """
    # Ensure index exists first
    ensure_result = await ais_service.ensure_index()

    results: list[dict[str, Any]] = []
    total_cu_ms = 0.0
    total_search_ms = 0.0
    succeeded = 0
    failed = 0

    for sample in samples:
        doc_result = await _process_single(sample)
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
                "total": len(samples),
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


async def _process_single(sample: str) -> dict[str, Any]:
    """Process a single document: read → CU extract → index."""
    try:
        file_bytes = read_sample(sample)
    except FileNotFoundError:
        return {"sample": sample, "error": f"Sample not found: {sample}"}

    # Build stable analyzer ID from field signatures
    field_sigs = sorted(f"{f['name']}:{f['type']}:{f['description']}" for f in BATCH_FIELDS)
    analyzer_id = "workshop_batch_" + hashlib.md5("|".join(field_sigs).encode()).hexdigest()[:12]

    # CU enrichment
    try:
        cu_result = await cu_service.analyze_custom(analyzer_id, file_bytes, sample, BATCH_FIELDS)
    except Exception as e:
        return {
            "sample": sample,
            "error": f"CU extraction failed: {e}",
            "cu_trace": None,
        }

    cu_fields = cu_result.get("result", {}).get("fields", {})
    cu_duration = cu_result.get("trace", {}).get("duration_ms", 0)

    # Build search document
    doc_id = hashlib.md5(f"batch_{sample}_{datetime.now(tz=UTC).isoformat()}".encode()).hexdigest()

    def _extract(fields: dict[str, Any], name: str) -> str:
        field = fields.get(name, {})
        if isinstance(field, dict):
            return field.get("valueString") or field.get("value") or field.get("content") or ""
        return str(field) if field else ""

    search_doc = {
        "id": doc_id,
        "title": sample,
        "content": cu_result.get("result", {}).get("content", ""),
        "summary": _extract(cu_fields, "summary"),
        "key_topics": _extract(cu_fields, "key_topics"),
        "source_doc": sample,
        "indexed_at": datetime.now(tz=UTC).isoformat(),
    }

    # Push to search index
    try:
        index_result = await ais_service.index_document(search_doc)
    except Exception as e:
        return {
            "sample": sample,
            "error": f"Search indexing failed: {e}",
            "cu_fields": {f["name"]: _extract(cu_fields, f["name"]) for f in BATCH_FIELDS},
            "cu_duration_ms": cu_duration,
            "cu_trace": cu_result.get("trace"),
        }

    search_duration = index_result.get("trace", {}).get("duration_ms", 0)

    return {
        "sample": sample,
        "document_id": doc_id,
        "cu_fields": {f["name"]: _extract(cu_fields, f["name"]) for f in BATCH_FIELDS},
        "cu_duration_ms": round(cu_duration, 2),
        "search_duration_ms": round(search_duration, 2),
        "cu_trace": cu_result.get("trace"),
        "search_trace": index_result.get("trace"),
    }
