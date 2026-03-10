"""AI Search router — index documents and search."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from workshop.routers.documents import read_sample
from workshop.services import ai_search as ais_service
from workshop.services import content_understanding as cu_service

router = APIRouter(prefix="/api/search", tags=["ai-search"])


class IndexRequest(BaseModel):
    """Request to index a document with CU enrichment."""

    sample: str
    fields: list[dict[str, str]] = [
        {
            "name": "summary",
            "type": "string",
            "description": "A 2-3 sentence summary of the document",
        },
        {"name": "key_topics", "type": "string", "description": "Main topics or themes"},
    ]


class SearchRequest(BaseModel):
    """Search query request."""

    query: str
    top: int = 5
    use_semantic: bool = True


@router.post("/ensure-index")
async def ensure_index() -> dict[str, Any]:
    """Create or update the search index schema."""
    return await ais_service.ensure_index()


@router.post("/index")
async def index_document(request: IndexRequest) -> dict[str, Any]:
    """Analyze a document with CU, then push enriched data to AI Search."""
    file_bytes, filename = await read_sample(request.sample)

    # Run CU custom extraction to get enriched fields
    analyzer_id = (
        "workshop_search_"
        + hashlib.md5("|".join(f["name"] for f in request.fields).encode()).hexdigest()[:12]
    )
    cu_result = await cu_service.analyze_custom(analyzer_id, file_bytes, filename, request.fields)

    # Build search document from CU results
    doc_id = hashlib.md5(f"{filename}_{datetime.now(tz=UTC).isoformat()}".encode()).hexdigest()
    fields_dict = cu_result.get("result", {}).get("fields", {})

    search_doc = {
        "id": doc_id,
        "title": filename,
        "content": cu_result.get("result", {}).get("content", ""),
        "summary": _extract_field(fields_dict, "summary"),
        "source_doc": filename,
        "indexed_at": datetime.now(tz=UTC).isoformat(),
    }

    # Push to search index
    index_result = await ais_service.index_document(search_doc)

    return {
        "result": {
            "cu_extraction": {
                "fields": {
                    k: _extract_field(fields_dict, k) for k in [f["name"] for f in request.fields]
                },
                "content_preview": (cu_result.get("result", {}).get("content") or "")[:500],
            },
            "indexing": index_result.get("result", {}),
            "document_id": doc_id,
        },
        "trace": {
            "cu": cu_result.get("trace", {}),
            "search": index_result.get("trace", {}),
        },
    }


@router.post("/query")
async def search(request: SearchRequest) -> dict[str, Any]:
    """Search the document index."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return await ais_service.search_documents(request.query, request.top, request.use_semantic)


@router.get("/stats")
async def index_stats() -> dict[str, Any]:
    """Get index statistics."""
    return await ais_service.get_index_stats()


def _extract_field(fields: dict[str, Any], name: str) -> str:
    """Extract a string value from CU fields response."""
    field = fields.get(name, {})
    if isinstance(field, dict):
        return field.get("valueString") or field.get("value") or field.get("content") or ""
    return str(field) if field else ""
