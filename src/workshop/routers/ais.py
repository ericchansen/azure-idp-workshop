"""AI Search router — index documents and search."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, ValidationError

from workshop.routers.documents import DocumentSource, get_document_source
from workshop.services import ai_search as ais_service
from workshop.services import content_understanding as cu_service
from workshop.services.cu_fields import extract_field_value

router = APIRouter(prefix="/api/search", tags=["ai-search"])


class IndexField(BaseModel):
    """A field to extract during CU enrichment."""

    name: str
    type: str = "string"
    description: str = ""


class IndexRequest(BaseModel):
    """Request to index a document with CU enrichment."""

    sample: str
    fields: list[IndexField] = [
        IndexField(
            name="summary",
            type="string",
            description="A 2-3 sentence summary of the document",
        ),
        IndexField(name="key_topics", type="string", description="Main topics or themes"),
    ]


class SearchRequest(BaseModel):
    """Search query request."""

    query: str
    top: int = 5
    use_semantic: bool = True
    upload_scope: str | None = None


@router.post("/ensure-index")
async def ensure_index() -> dict[str, Any]:
    """Create or update the search index schema."""
    return await ais_service.ensure_index()


@router.post("/index")
async def index_document(
    request: Request,
    file: Annotated[UploadFile | None, File()] = None,
    sample: Annotated[str | None, Form()] = None,
    fields: Annotated[str | None, Form()] = None,
    upload_scope: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    """Analyze a document with CU, then push enriched data to AI Search."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await _read_index_json(request)
        document = await get_document_source(sample=body.sample)
        return await _index_document_source(document, body.fields)

    document = await get_document_source(file=file, sample=sample)
    if document.source_type == "upload" and not upload_scope:
        raise HTTPException(
            status_code=400, detail="Provide 'upload_scope' when indexing an uploaded document"
        )
    return await _index_document_source(document, _parse_index_fields(fields), upload_scope)


async def _index_document_source(
    document: DocumentSource, fields: list[IndexField], upload_scope: str | None = None
) -> dict[str, Any]:
    # Run CU custom extraction to get enriched fields
    # Build a stable, schema-sensitive analyzer ID from name, type, and description.
    field_signatures = sorted(f"{f.name}:{f.type}:{f.description}" for f in fields)
    analyzer_id = (
        "workshop_search_" + hashlib.md5("|".join(field_signatures).encode()).hexdigest()[:12]
    )
    cu_result = await cu_service.analyze_custom(
        analyzer_id,
        document.content,
        document.filename,
        [{"name": f.name, "type": f.type, "description": f.description} for f in fields],
    )

    # Build search document from CU results
    doc_id = ais_service.build_document_id(_search_id_source(document, upload_scope))
    fields_dict = cu_result.get("result", {}).get("fields", {})

    search_doc = {
        "id": doc_id,
        "title": document.filename,
        "content": cu_result.get("result", {}).get("content", ""),
        "summary": _extract_field(fields_dict, "summary"),
        "key_topics": _extract_field(fields_dict, "key_topics"),
        "source_doc": document.filename,
        "source_type": document.source_type,
        "upload_scope": upload_scope if document.source_type == "upload" else "",
        "indexed_at": datetime.now(tz=UTC).isoformat(),
    }

    # Push to search index
    index_result = await ais_service.index_document(search_doc)

    return {
        "result": {
            "cu_extraction": {
                "fields": {k: _extract_field(fields_dict, k) for k in [f.name for f in fields]},
                "content_preview": (cu_result.get("result", {}).get("content") or "")[:500],
            },
            "indexing": index_result.get("result", {}),
            "document_id": doc_id,
            "source_doc": document.filename,
            "source_type": document.source_type,
        },
        "trace": {
            "cu": cu_result.get("trace", {}),
            "search": index_result.get("trace", {}),
        },
    }


async def _read_index_json(request: Request) -> IndexRequest:
    try:
        payload = await request.json()
        return IndexRequest.model_validate(payload)
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from err
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=err.errors()) from err


def _parse_index_fields(fields: str | None) -> list[IndexField]:
    if not fields:
        return IndexRequest(sample="upload").fields
    try:
        payload = json.loads(fields)
        return [IndexField.model_validate(field) for field in payload]
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Field definitions must be valid JSON") from err
    except (TypeError, ValidationError) as err:
        raise HTTPException(status_code=422, detail="Field definitions are invalid") from err


def _search_id_source(document: DocumentSource, upload_scope: str | None) -> str:
    if document.source_type != "upload":
        return document.id_source
    return f"{document.id_source}:scope:{upload_scope}"


@router.post("/query")
async def search(request: SearchRequest) -> dict[str, Any]:
    """Search the document index."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return await ais_service.search_documents(
        request.query, request.top, request.use_semantic, request.upload_scope
    )


@router.get("/stats")
async def index_stats() -> dict[str, Any]:
    """Get index statistics."""
    return await ais_service.get_index_stats()


def _extract_field(fields: dict[str, Any], name: str) -> str:
    """Extract a string value from CU fields response."""
    return extract_field_value(fields, name)
