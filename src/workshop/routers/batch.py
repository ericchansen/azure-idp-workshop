"""Batch processing router — process multiple documents in sequence."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, ValidationError

from workshop.routers.documents import DocumentSource, get_document_source
from workshop.services import batch as batch_service

router = APIRouter(prefix="/api/batch", tags=["batch"])

MAX_BATCH_SIZE = 20


class BatchRequest(BaseModel):
    """Request to batch-process documents."""

    samples: list[str]

    @property
    def deduplicated(self) -> list[str]:
        """Return unique samples preserving order."""
        return list(dict.fromkeys(self.samples))


@router.post("/process")
async def batch_process(
    request: Request,
    files: Annotated[list[UploadFile] | None, File()] = None,
    samples: Annotated[str | None, Form()] = None,
    upload_scope: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    """Process multiple documents: CU enrichment + Search indexing."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await _read_batch_json(request)
        sample_names = body.deduplicated
        _validate_batch_count(len(sample_names), empty_detail="No samples provided")
        return await batch_service.process_batch(sample_names)

    sample_names = list(dict.fromkeys(_parse_form_samples(samples)))
    upload_files = files or []
    _validate_batch_count(
        len(sample_names) + len(upload_files), empty_detail="No documents provided"
    )
    if upload_files and not upload_scope:
        raise HTTPException(
            status_code=400, detail="Provide 'upload_scope' when indexing uploaded documents"
        )
    upload_sources = [await get_document_source(file=file) for file in upload_files]
    items = _deduplicate_items([*sample_names, *upload_sources])
    return await batch_service.process_batch_items(items, upload_scope)


async def _read_batch_json(request: Request) -> BatchRequest:
    try:
        payload = await request.json()
        return BatchRequest.model_validate(payload)
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from err
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=err.errors()) from err


def _parse_form_samples(samples: str | None) -> list[str]:
    if not samples:
        return []
    try:
        payload = json.loads(samples)
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Samples must be a JSON array") from err
    if not isinstance(payload, list) or not all(isinstance(sample, str) for sample in payload):
        raise HTTPException(status_code=422, detail="Samples must be a JSON array of strings")
    return payload


def _deduplicate_items(items: list[str | DocumentSource]) -> list[str | DocumentSource]:
    seen: set[str] = set()
    deduplicated: list[str | DocumentSource] = []
    for item in items:
        key = item if isinstance(item, str) else item.id_source
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(item)
    return deduplicated


def _validate_batch_count(count: int, empty_detail: str) -> None:
    if not count:
        raise HTTPException(status_code=400, detail=empty_detail)
    if count > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {count} exceeds maximum of {MAX_BATCH_SIZE}",
        )
