"""Analyzer definitions for the CU-only patient log demo."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

PATIENT_LOG_CLASSIFIER_ID = "patient_log_classifier"
PATIENT_LOG_TREATMENT_ID = "patient_log_treatment"


def get_patient_log_analyzer_definitions(
    completion_model: str = "gpt-5.2",
    embedding_model: str = "text-embedding-3-large",
) -> dict[str, dict[str, Any]]:
    """Return Content Understanding analyzer definitions for the patient log demo."""
    return {
        PATIENT_LOG_TREATMENT_ID: _treatment_log_analyzer(completion_model, embedding_model),
        PATIENT_LOG_CLASSIFIER_ID: _classifier_analyzer(completion_model),
    }


def get_patient_log_analyzer_definition(
    analyzer_id: str,
    completion_model: str = "gpt-5.2",
    embedding_model: str = "text-embedding-3-large",
) -> dict[str, Any]:
    """Return a copy of a single patient log analyzer definition."""
    definitions = get_patient_log_analyzer_definitions(completion_model, embedding_model)
    return deepcopy(definitions[analyzer_id])


def _treatment_log_analyzer(completion_model: str, embedding_model: str) -> dict[str, Any]:
    return {
        "description": "CU-only analyzer for scanned patient treatment logs and body diagrams.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {
            "completion": completion_model,
            "embedding": embedding_model,
        },
        "config": {
            "returnDetails": True,
            "enableFormula": False,
            "estimateFieldSourceAndConfidence": True,
            "tableFormat": "html",
        },
        "fieldSchema": {
            "fields": {
                "document_instance_id": {
                    "type": "string",
                    "method": "generate",
                    "description": (
                        "Stable label for this treatment log instance, such as page range, "
                        "copy number, or visible form identifier."
                    ),
                },
                "patient_identifiers_present": {
                    "type": "string",
                    "method": "generate",
                    "description": (
                        "Describe whether patient identifiers are present without reproducing "
                        "sensitive values. Use values like present, absent, or unclear."
                    ),
                },
                "provider_or_clinic": {
                    "type": "string",
                    "method": "generate",
                    "description": "Provider, therapist, clinic, or facility name if visible.",
                },
                "service_period": {
                    "type": "string",
                    "method": "generate",
                    "description": (
                        "Service date range, month, or treatment period covered by the log."
                    ),
                },
                "visit_entries": {
                    "type": "array",
                    "method": "generate",
                    "description": (
                        "Each treatment row or visit entry visible in the log, including date, "
                        "services selected, provider initials, patient signature, and notes."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "method": "generate",
                                "description": "Visit date or row date as displayed.",
                            },
                            "services_or_modalities": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Checked services, modalities, or treatment activities."
                                ),
                            },
                            "initials_or_signature_present": {
                                "type": "string",
                                "method": "generate",
                                "description": "Whether initials or signature evidence is visible.",
                            },
                            "row_confidence": {
                                "type": "string",
                                "method": "classify",
                                "enum": ["high", "medium", "low", "unclear"],
                                "description": "Confidence in the row interpretation.",
                            },
                            "ambiguity_note": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Any uncertainty about the row, mark, date, or signature."
                                ),
                            },
                        },
                    },
                },
                "body_diagram_findings": {
                    "type": "array",
                    "method": "generate",
                    "description": (
                        "Visual findings from body diagrams, including circled or drawn regions, "
                        "body view, laterality, and symptom interpretation if visible."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_page_or_segment": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Page, segment, or visible area where the mark appears."
                                ),
                            },
                            "body_view": {
                                "type": "string",
                                "method": "classify",
                                "enum": [
                                    "anterior",
                                    "posterior",
                                    "left_lateral",
                                    "right_lateral",
                                    "spine",
                                    "unclear",
                                ],
                                "description": "Body view where the finding appears.",
                            },
                            "region": {
                                "type": "string",
                                "method": "generate",
                                "description": "Anatomical region or spinal level range marked.",
                            },
                            "mark_type": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Circle, oval, arrow, handwritten mark, checkbox, or other "
                                    "visual mark."
                                ),
                            },
                            "symptom_interpretation": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Symptom implied by the form legend or nearby text, such as "
                                    "pain, spasm, edema, ache, burning, or tingling. Say unclear "
                                    "when not supported."
                                ),
                            },
                            "confidence": {
                                "type": "string",
                                "method": "classify",
                                "enum": ["high", "medium", "low", "unclear"],
                                "description": "Confidence in the visual interpretation.",
                            },
                            "ambiguity_note": {
                                "type": "string",
                                "method": "generate",
                                "description": "Why this visual finding is ambiguous or reliable.",
                            },
                        },
                    },
                },
                "spinal_palpation_findings": {
                    "type": "array",
                    "method": "generate",
                    "description": (
                        "Spinal palpation annotations, including marked levels like C4-C6, arrows, "
                        "lines, checks, or other visible indicators."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "level_or_range": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Spinal level or range associated with the visual mark."
                                ),
                            },
                            "mark_description": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Description of the visible mark near the spinal level."
                                ),
                            },
                            "confidence": {
                                "type": "string",
                                "method": "classify",
                                "enum": ["high", "medium", "low", "unclear"],
                                "description": "Confidence in the level interpretation.",
                            },
                        },
                    },
                },
                "missing_or_incomplete_entries": {
                    "type": "array",
                    "method": "generate",
                    "description": (
                        "Rows or sections that appear incomplete, including missing dates, "
                        "signatures, service selections, or unclear handwritten entries."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "method": "generate",
                                "description": (
                                    "Page, segment, row, or section where the gap appears."
                                ),
                            },
                            "issue": {
                                "type": "string",
                                "method": "generate",
                                "description": "Missing or incomplete information observed.",
                            },
                            "severity": {
                                "type": "string",
                                "method": "classify",
                                "enum": ["high", "medium", "low"],
                                "description": "How important the missing information appears.",
                            },
                        },
                    },
                },
                "overall_summary": {
                    "type": "string",
                    "method": "generate",
                    "description": (
                        "Short summary of the treatment log, visible body diagram findings, "
                        "missing information, and notable uncertainties."
                    ),
                },
                "ambiguities": {
                    "type": "array",
                    "method": "generate",
                    "description": "Key uncertainties that should be reviewed by a human.",
                    "items": {"type": "string"},
                },
            }
        },
    }


def _classifier_analyzer(completion_model: str) -> dict[str, Any]:
    return {
        "description": "Segment and route scanned patient log packets by document type.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": completion_model},
        "config": {
            "returnDetails": True,
            "enableSegment": True,
            "omitContent": True,
            "contentCategories": {
                "patient_treatment_log": {
                    "description": (
                        "Treatment log or attendance chart pages with visit rows, service "
                        "checkboxes, patient/provider signatures, or body diagram sections."
                    ),
                    "analyzerId": PATIENT_LOG_TREATMENT_ID,
                },
                "palpation_body_diagram": {
                    "description": (
                        "Pages or segments dominated by body diagrams, palpation drawings, "
                        "spinal level markings, or symptom legends."
                    ),
                    "analyzerId": PATIENT_LOG_TREATMENT_ID,
                },
                "claim_or_cover_sheet": {
                    "description": (
                        "Claim packet cover sheets, fax covers, or administrative summary pages."
                    ),
                },
                "invoice_or_billing": {
                    "description": "Invoices, billing statements, or payment request documents.",
                },
                "correspondence": {
                    "description": "Letters, notes, emails, or other correspondence pages.",
                },
                "other": {
                    "description": "Any content that does not match the patient log categories.",
                },
            },
        },
    }
