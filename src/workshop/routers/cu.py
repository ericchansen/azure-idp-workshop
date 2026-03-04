"""Content Understanding API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from workshop.routers.documents import get_file_bytes, read_sample
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
async def cu_custom(request: CustomAnalyzeRequest) -> dict[str, Any]:
    """Run a CU custom analyzer with user-defined fields."""
    if not request.sample:
        raise HTTPException(status_code=400, detail="Provide 'sample' name in request body")

    try:
        file_bytes = read_sample(request.sample)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Sample '{request.sample}' not found"
        ) from None

    fields = [f.model_dump() for f in request.fields] if request.fields else None
    return await cu_service.analyze_custom(request.analyzer_id, file_bytes, request.sample, fields)
