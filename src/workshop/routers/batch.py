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

    @property
    def deduplicated(self) -> list[str]:
        """Return unique samples preserving order."""
        seen: set[str] = set()
        return [s for s in self.samples if not (s in seen or seen.add(s))]  # type: ignore[func-returns-value]


MAX_BATCH_SIZE = 20


@router.post("/process")
async def batch_process(request: BatchRequest) -> dict[str, Any]:
    """Process multiple documents: CU enrichment + Search indexing."""
    samples = request.deduplicated
    if not samples:
        return {"result": {"documents": [], "summary": {"total": 0, "succeeded": 0, "failed": 0}}}
    if len(samples) > MAX_BATCH_SIZE:
        return {
            "result": {"documents": [], "summary": {"total": 0, "succeeded": 0, "failed": 0}},
            "error": f"Batch size {len(samples)} exceeds maximum of {MAX_BATCH_SIZE}",
        }
    return await batch_service.process_batch(samples)
