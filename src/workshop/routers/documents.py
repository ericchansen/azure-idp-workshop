"""Document management endpoints — list samples, handle uploads."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import Response

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Path to bundled sample documents
SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"

# 10 MB upload limit — container has only 1Gi memory
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024

SUPPORTED_DOCUMENT_EXTENSIONS = {
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

SUPPORTED_DOCUMENT_FORMATS_LABEL = "PDF, JPEG, PNG, BMP, TIFF, HEIF, DOCX, XLSX, PPTX, HTML"


@dataclass(frozen=True)
class DocumentSource:
    """A request-scoped document, from either a bundled sample or an upload."""

    content: bytes
    filename: str
    id_source: str
    source_type: str
    content_type: str | None = None
    content_hash: str | None = None


def _resolve_sample_path(filename: str) -> Path:
    """Resolve a sample filename to a safe path within SAMPLES_DIR.

    Raises HTTP 400 if the resolved path escapes the samples directory.
    """
    path = (SAMPLES_DIR / filename).resolve()
    if not path.is_relative_to(SAMPLES_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    return path


def normalize_filename(filename: str | None) -> str:
    """Return a safe display filename without path components or control chars."""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    return name or "upload"


def validate_document_extension(filename: str, service_name: str = "Uploaded documents") -> None:
    """Raise 400 if a filename has an unsupported extension."""
    ext = Path(filename).suffix.lower()
    if ext and ext in SUPPORTED_DOCUMENT_EXTENSIONS:
        return
    if not ext:
        detail = (
            f"{service_name} requires a supported file extension. "
            f"Supported formats: {SUPPORTED_DOCUMENT_FORMATS_LABEL}."
        )
    else:
        detail = (
            f"{service_name} does not support '{ext}' files. "
            f"Supported formats: {SUPPORTED_DOCUMENT_FORMATS_LABEL}."
        )
    raise HTTPException(status_code=400, detail=detail)


def _enforce_upload_size(content: bytes) -> None:
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")


async def read_upload(file: UploadFile) -> tuple[bytes, str]:
    """Read and validate an uploaded document without storing it."""
    filename = normalize_filename(file.filename)
    validate_document_extension(filename)
    chunks: list[bytes] = []
    total_size = 0
    while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
            )
        chunks.append(chunk)
    content = b"".join(chunks)
    _enforce_upload_size(content)
    return content, filename


def build_upload_id_source(filename: str, content: bytes) -> tuple[str, str]:
    """Build a deterministic identity from uploaded filename and content."""
    digest = hashlib.sha256(content).hexdigest()
    return f"upload:{filename}:{digest[:16]}", digest


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
    """Validate an uploaded document and return metadata without storing bytes."""
    content, filename = await read_upload(file)
    return {
        "filename": filename,
        "size_bytes": len(content),
        "content_type": file.content_type,
        "source_type": "upload",
    }


def read_sample(filename: str) -> bytes:
    """Read a sample document's bytes. Used internally by other routers."""
    path = _resolve_sample_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Sample document not found: {filename}")
    return path.read_bytes()


def get_sample_document_source(sample: str) -> DocumentSource:
    """Read a bundled sample into a request-scoped document source."""
    return DocumentSource(
        content=read_sample(sample),
        filename=sample,
        id_source=sample,
        source_type="sample",
        content_type=mimetypes.guess_type(sample)[0],
    )


async def get_file_bytes(file: UploadFile | None, sample: str | None) -> tuple[bytes, str]:
    """Extract file bytes from upload or sample name, with size limit enforcement."""
    source = await get_document_source(file=file, sample=sample)
    return source.content, source.filename


async def get_document_source(
    file: UploadFile | None = None, sample: str | None = None
) -> DocumentSource:
    """Extract a request-scoped document source from an upload or sample name."""
    if file:
        content, filename = await read_upload(file)
        id_source, digest = build_upload_id_source(filename, content)
        return DocumentSource(
            content=content,
            filename=filename,
            id_source=id_source,
            source_type="upload",
            content_type=file.content_type,
            content_hash=digest,
        )
    if sample:
        try:
            return get_sample_document_source(sample)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Sample '{sample}' not found") from None
    raise HTTPException(status_code=400, detail="Provide 'file' upload or 'sample' name")
