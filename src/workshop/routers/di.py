"""Document Intelligence API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile

from workshop.routers.documents import read_sample
from workshop.services import document_intelligence as di_service

router = APIRouter(prefix="/api/di", tags=["document-intelligence"])

# Formats supported by Azure DI Layout API
DI_SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".jpeg",
    ".jpg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".heif",
    ".heic",
    ".docx",
    ".xlsx",
    ".pptx",
    ".html",
}


def _validate_format(filename: str) -> None:
    """Raise 400 if the file format is not supported by Document Intelligence."""
    import os

    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in DI_SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Document Intelligence does not support '{ext}' files. "
                f"Supported formats: PDF, JPEG, PNG, BMP, TIFF, HEIF, DOCX, XLSX, PPTX, HTML."
            ),
        )


@router.post("/layout")
async def di_layout(file: UploadFile | None = None, sample: str | None = None) -> dict[str, Any]:
    """Run DI Layout analysis on an uploaded or sample document."""
    file_bytes, filename = await _get_file_bytes(file, sample)
    _validate_format(filename)
    return di_service.analyze_layout(file_bytes, filename)


@router.post("/prebuilt/{model_id}")
async def di_prebuilt(
    model_id: str, file: UploadFile | None = None, sample: str | None = None
) -> dict[str, Any]:
    """Run a DI prebuilt model (prebuilt-invoice, prebuilt-receipt, etc.)."""
    allowed = {"prebuilt-invoice", "prebuilt-receipt", "prebuilt-read", "prebuilt-layout"}
    if model_id not in allowed:
        raise HTTPException(
            status_code=400, detail=f"Model '{model_id}' not supported. Use: {allowed}"
        )

    file_bytes, filename = await _get_file_bytes(file, sample)
    _validate_format(filename)
    return di_service.analyze_prebuilt(model_id, file_bytes, filename)


async def _get_file_bytes(file: UploadFile | None, sample: str | None) -> tuple[bytes, str]:
    """Extract file bytes from upload or sample name."""
    if file:
        content = await file.read()
        return content, file.filename or "upload"
    if sample:
        try:
            return read_sample(sample), sample
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Sample '{sample}' not found") from None
    raise HTTPException(status_code=400, detail="Provide 'file' upload or 'sample' name")
