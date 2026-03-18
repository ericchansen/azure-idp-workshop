"""Batch processing router — process multiple documents in sequence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
async def batch_process(request: BatchRequest) -> dict[str, Any]:
    """Process multiple documents: CU enrichment + Search indexing."""
    samples = request.deduplicated
    if not samples:
        raise HTTPException(status_code=400, detail="No samples provided")
    if len(samples) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size {len(samples)} exceeds maximum of {MAX_BATCH_SIZE}",
        )
    return await batch_service.process_batch(samples)
