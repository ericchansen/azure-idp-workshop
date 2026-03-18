"""Batch processing router — process multiple documents in sequence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from workshop.services import batch as batch_service

router = APIRouter(prefix="/api/batch", tags=["batch"])


class BatchRequest(BaseModel):
    """Request to batch-process documents."""

    samples: list[str]


@router.post("/process")
async def batch_process(request: BatchRequest) -> dict[str, Any]:
    """Process multiple documents: CU enrichment + Search indexing."""
    if not request.samples:
        return {"result": {"documents": [], "summary": {"total": 0, "succeeded": 0, "failed": 0}}}
    return await batch_service.process_batch(request.samples)
