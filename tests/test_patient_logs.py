"""Patient log analyzer demo tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from workshop.services.patient_log_analyzers import (
    PATIENT_LOG_CLASSIFIER_ID,
    PATIENT_LOG_TREATMENT_ID,
    get_patient_log_analyzer_definitions,
)


def test_patient_log_analyzer_definitions_include_segmenter_and_extractor() -> None:
    definitions = get_patient_log_analyzer_definitions()

    classifier = definitions[PATIENT_LOG_CLASSIFIER_ID]
    treatment = definitions[PATIENT_LOG_TREATMENT_ID]

    assert classifier["config"]["enableSegment"] is True
    assert (
        classifier["config"]["contentCategories"]["patient_treatment_log"]["analyzerId"]
        == PATIENT_LOG_TREATMENT_ID
    )
    assert "body_diagram_findings" in treatment["fieldSchema"]["fields"]
    assert "spinal_palpation_findings" in treatment["fieldSchema"]["fields"]
    assert treatment["baseAnalyzerId"] == "prebuilt-document"


def test_patient_log_page_renders(client):  # type: ignore[no-untyped-def]
    resp = client.get("/patient-log")
    assert resp.status_code == 200
    assert "Patient Treatment Log Analyzer" in resp.text
    assert "Module 1" not in resp.text


def test_analyzer_definitions_endpoint(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/patient-logs/analyzer-definitions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["classifier_analyzer_id"] == PATIENT_LOG_CLASSIFIER_ID
    assert PATIENT_LOG_TREATMENT_ID in body["result"]["definitions"]


def test_ensure_patient_log_analyzers(client):  # type: ignore[no-untyped-def]
    with (
        patch("workshop.routers.patient_logs.settings.admin_api_key", "test-admin-key"),
        patch(
            "workshop.routers.patient_logs.cu_service.create_or_replace_analyzer",
            AsyncMock(return_value={"result": {}, "trace": {"response": {"status": 200}}}),
        ) as mock_create,
    ):
        resp = client.post(
            "/api/patient-logs/ensure-analyzers",
            headers={"X-Admin-Key": "test-admin-key"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["ready"] is True
    assert mock_create.call_count == 2
    assert mock_create.call_args_list[0].args[0] == PATIENT_LOG_TREATMENT_ID
    assert mock_create.call_args_list[1].args[0] == PATIENT_LOG_CLASSIFIER_ID


def test_ensure_patient_log_analyzers_requires_admin_key(client):  # type: ignore[no-untyped-def]
    with patch("workshop.routers.patient_logs.settings.admin_api_key", "test-admin-key"):
        resp = client.post("/api/patient-logs/ensure-analyzers")

    assert resp.status_code == 403
    assert "admin" in resp.json()["detail"].lower()


def test_ensure_patient_log_analyzers_disabled_without_admin_key(client):  # type: ignore[no-untyped-def]
    with patch("workshop.routers.patient_logs.settings.admin_api_key", ""):
        resp = client.post("/api/patient-logs/ensure-analyzers")

    assert resp.status_code == 403
    assert "disabled" in resp.json()["detail"].lower()


def test_analyze_patient_log_upload(client):  # type: ignore[no-untyped-def]
    with patch(
        "workshop.routers.patient_logs.cu_service.analyze_binary_with_analyzer",
        AsyncMock(
            return_value={
                "result": {
                    "fields": {
                        "overall_summary": {"value": "Treatment log with body diagram marks"}
                    }
                },
                "trace": {"response": {"status": 200}},
            }
        ),
    ) as mock_analyze:
        resp = client.post(
            "/api/patient-logs/analyze",
            files={"file": ("patient-log.pdf", b"%PDF-1.4\n", "application/pdf")},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["filename"] == "patient-log.pdf"
    assert body["result"]["analyzer_id"] == PATIENT_LOG_CLASSIFIER_ID
    assert mock_analyze.call_args.args[0] == PATIENT_LOG_CLASSIFIER_ID


def test_analyze_patient_log_rejects_unsupported_upload(client):  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/patient-logs/analyze",
        files={"file": ("patient-log.txt", b"not supported", "text/plain")},
    )
    assert resp.status_code == 400
    assert "does not support" in resp.json()["detail"]
