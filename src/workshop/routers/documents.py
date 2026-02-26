"""Document management endpoints — list samples, handle uploads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Path to bundled sample documents
SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"


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


@router.get("/samples/{filename}")
def get_sample(filename: str) -> dict[str, str]:
    """Get the path to a sample document (for internal use)."""
    path = SAMPLES_DIR / filename
    if not path.exists() or not path.is_file():
        return {"error": f"Sample '{filename}' not found"}
    return {"path": str(path), "name": filename}


@router.post("/upload")
async def upload_document(file: UploadFile) -> dict[str, Any]:
    """Accept an uploaded document and return its bytes (ephemeral, not stored)."""
    content = await file.read()
    return {
        "filename": file.filename or "unknown",
        "size_bytes": len(content),
        "content_type": file.content_type,
    }


def read_sample(filename: str) -> bytes:
    """Read a sample document's bytes. Used internally by other routers."""
    path = SAMPLES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Sample document not found: {filename}")
    return path.read_bytes()
