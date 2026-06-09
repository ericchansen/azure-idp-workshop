"""CU-only patient treatment log analyzer endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from workshop.config import settings
from workshop.routers.documents import get_document_source
from workshop.services import content_understanding as cu_service
from workshop.services.patient_log_analyzers import (
    PATIENT_LOG_CLASSIFIER_ID,
    PATIENT_LOG_TREATMENT_ID,
    get_patient_log_analyzer_definitions,
)

router = APIRouter(prefix="/api/patient-logs", tags=["patient-logs"])


@router.get("/analyzer-definitions")
def analyzer_definitions() -> dict[str, Any]:
    """Return the analyzer definitions used by the patient log demo."""
    definitions = _definitions()
    return {
        "result": {
            "classifier_analyzer_id": PATIENT_LOG_CLASSIFIER_ID,
            "treatment_analyzer_id": PATIENT_LOG_TREATMENT_ID,
            "definitions": definitions,
        }
    }


@router.post("/ensure-analyzers")
async def ensure_analyzers(x_admin_key: Annotated[str | None, Header()] = None) -> dict[str, Any]:
    """Create or update the patient log analyzers in Content Understanding."""
    _require_admin(x_admin_key)
    definitions = _definitions()
    treatment = await cu_service.create_or_replace_analyzer(
        PATIENT_LOG_TREATMENT_ID, definitions[PATIENT_LOG_TREATMENT_ID]
    )
    classifier = await cu_service.create_or_replace_analyzer(
        PATIENT_LOG_CLASSIFIER_ID, definitions[PATIENT_LOG_CLASSIFIER_ID]
    )
    has_error = bool(
        treatment.get("trace", {}).get("error") or classifier.get("trace", {}).get("error")
    )
    return {
        "result": {
            "ready": not has_error,
            "analyzers": [
                {
                    "id": PATIENT_LOG_TREATMENT_ID,
                    "kind": "treatment-log extractor",
                    "status": "error" if treatment.get("trace", {}).get("error") else "ready",
                },
                {
                    "id": PATIENT_LOG_CLASSIFIER_ID,
                    "kind": "classifier/segmenter-router",
                    "status": "error" if classifier.get("trace", {}).get("error") else "ready",
                },
            ],
        },
        "trace": {
            PATIENT_LOG_TREATMENT_ID: treatment.get("trace", {}),
            PATIENT_LOG_CLASSIFIER_ID: classifier.get("trace", {}),
        },
    }


@router.post("/analyze")
async def analyze_patient_log(file: Annotated[UploadFile, File()]) -> dict[str, Any]:
    """Analyze an uploaded patient treatment log packet without storing it."""
    document = await get_document_source(file=file)
    result = await cu_service.analyze_binary_with_analyzer(
        PATIENT_LOG_CLASSIFIER_ID,
        document.content,
        document.filename,
        document.content_type or "application/octet-stream",
    )
    return {
        "result": {
            "filename": document.filename,
            "analyzer_id": PATIENT_LOG_CLASSIFIER_ID,
            "analysis": result.get("result", {}),
        },
        "trace": result.get("trace", {}),
    }


def _definitions() -> dict[str, dict[str, Any]]:
    return get_patient_log_analyzer_definitions(
        completion_model=settings.cu_completion_model,
        embedding_model=settings.cu_embedding_model,
    )


def _require_admin(admin_key: str | None) -> None:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=403,
            detail="Analyzer creation is disabled until ADMIN_API_KEY is configured.",
        )
    if admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid admin key.")
