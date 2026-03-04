"""Document management endpoints — list samples, handle uploads."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Path to bundled sample documents
SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"

# 10 MB upload limit — container has only 1Gi memory
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def _resolve_sample_path(filename: str) -> Path:
    """Resolve a sample filename to a safe path within SAMPLES_DIR.

    Raises HTTP 400 if the resolved path escapes the samples directory.
    """
    path = (SAMPLES_DIR / filename).resolve()
    if not path.is_relative_to(SAMPLES_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return path


@router.get("/samples")
def list_samples() -> list[dict[str, Any]]:
    """List available sample documents."""
    samples = []
    if SAMPLES_DIR.exists():
        for f in sorted(SAMPLES_DIR.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                samples.append(
                    {
                        "name": f.name,
                        "size_bytes": f.stat().st_size,
                        "extension": f.suffix.lower(),
                    }
                )
    return samples


@router.get("/samples/{filename}/raw")
def get_sample_raw(filename: str) -> Response:
    """Serve a sample document's raw bytes with correct MIME type."""
    path = _resolve_sample_path(filename)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found")
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return Response(content=path.read_bytes(), media_type=mime_type)


@router.get("/samples/{filename}")
def get_sample(filename: str) -> dict[str, str]:
    """Get the path to a sample document (for internal use)."""
    path = _resolve_sample_path(filename)
    if not path.exists() or not path.is_file():
        return {"error": f"Sample '{filename}' not found"}
    return {"path": str(path), "name": filename}


@router.post("/upload")
async def upload_document(file: UploadFile) -> dict[str, Any]:
    """Accept an uploaded document and return its bytes (ephemeral, not stored)."""
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )
    return {
        "filename": file.filename or "unknown",
        "size_bytes": len(content),
        "content_type": file.content_type,
    }


def read_sample(filename: str) -> bytes:
    """Read a sample document's bytes. Used internally by other routers."""
    path = _resolve_sample_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Sample document not found: {filename}")
    return path.read_bytes()


async def get_file_bytes(file: UploadFile | None, sample: str | None) -> tuple[bytes, str]:
    """Extract file bytes from upload or sample name, with size limit enforcement."""
    if file:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
            )
        return content, file.filename or "upload"
    if sample:
        try:
            return read_sample(sample), sample
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Sample '{sample}' not found") from None
    raise HTTPException(status_code=400, detail="Provide 'file' upload or 'sample' name")
