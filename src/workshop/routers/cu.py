"""Content Understanding API endpoints."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, ValidationError

from workshop.routers.documents import get_document_source, get_file_bytes
from workshop.services import content_understanding as cu_service

router = APIRouter(prefix="/api/cu", tags=["content-understanding"])


class CustomField(BaseModel):
    name: str
    type: str = "string"
    description: str = ""


class CustomAnalyzeRequest(BaseModel):
    analyzer_id: str = "workshop-custom"
    sample: str | None = None
    fields: list[CustomField] = []


@router.post("/layout")
async def cu_layout(file: UploadFile | None = None, sample: str | None = None) -> dict[str, Any]:
    """Run CU Layout analysis on an uploaded or sample document."""
    file_bytes, filename = await get_file_bytes(file, sample)
    return await cu_service.analyze_layout(file_bytes, filename)


@router.post("/prebuilt/{model_id}")
async def cu_prebuilt(
    model_id: str, file: UploadFile | None = None, sample: str | None = None
) -> dict[str, Any]:
    """Run a CU prebuilt analyzer (prebuilt-invoice, prebuilt-receipt, etc.)."""
    allowed = {"prebuilt-invoice", "prebuilt-receipt", "prebuilt-layout", "prebuilt-read"}
    if model_id not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Analyzer '{model_id}' not supported. Use: {allowed}"
        )

    file_bytes, filename = await get_file_bytes(file, sample)
    return await cu_service.analyze_prebuilt(model_id, file_bytes, filename)


@router.post("/custom")
async def cu_custom(
    request: Request,
    file: Annotated[UploadFile | None, File()] = None,
    sample: Annotated[str | None, Form()] = None,
    fields: Annotated[str | None, Form()] = None,
    analyzer_id: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    """Run a CU custom analyzer with user-defined fields."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        body = await _read_custom_json(request)
        document = await get_document_source(sample=body.sample)
        field_values = [f.model_dump() for f in body.fields] if body.fields else None
        return await cu_service.analyze_custom(
            body.analyzer_id, document.content, document.filename, field_values
        )

    document = await get_document_source(file=file, sample=sample)
    parsed_fields = _parse_custom_fields(fields)
    return await cu_service.analyze_custom(
        analyzer_id or "workshop-custom",
        document.content,
        document.filename,
        parsed_fields,
    )


async def _read_custom_json(request: Request) -> CustomAnalyzeRequest:
    try:
        payload = await request.json()
        body = CustomAnalyzeRequest.model_validate(payload)
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from err
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=err.errors()) from err
    if not body.sample:
        raise HTTPException(status_code=400, detail="Provide 'sample' name in request body")
    return body


def _parse_custom_fields(fields: str | None) -> list[dict[str, Any]] | None:
    if not fields:
        return None
    try:
        payload = json.loads(fields)
        parsed = [CustomField.model_validate(field).model_dump() for field in payload]
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=400, detail="Field definitions must be valid JSON") from err
    except (TypeError, ValidationError) as err:
        raise HTTPException(status_code=422, detail="Field definitions are invalid") from err
    return parsed
