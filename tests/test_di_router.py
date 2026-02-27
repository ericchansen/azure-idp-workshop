"""DI router tests (mocked — no real Azure calls)."""

from workshop.services.document_intelligence import _summarize_result


def test_di_layout_requires_file_or_sample(client):  # type: ignore[no-untyped-def]
    resp = client.post("/api/di/layout")
    assert resp.status_code == 400


def test_di_prebuilt_rejects_unknown_model(client):  # type: ignore[no-untyped-def]
    resp = client.post("/api/di/prebuilt/unknown-model")
    assert resp.status_code == 400


def test_di_prebuilt_accepts_valid_model_names(client):  # type: ignore[no-untyped-def]
    valid = ["prebuilt-invoice", "prebuilt-receipt", "prebuilt-read", "prebuilt-layout"]
    for model in valid:
        # Will fail with 400 (no file) not 400 (bad model)
        resp = client.post(f"/api/di/prebuilt/{model}")
        assert resp.status_code == 400
        assert "Provide" in resp.json()["detail"]


def test_summarize_result_includes_document_confidence() -> None:
    """_summarize_result includes document-level confidence score."""
    result = {
        "documents": [
            {
                "docType": "invoice",
                "confidence": 0.95,
                "fields": {
                    "VendorName": {"content": "Contoso", "confidence": 0.99},
                    "Total": {"value": "100.00", "confidence": 0.92},
                },
            }
        ],
    }
    summary = _summarize_result(result)
    assert summary["confidence"] == 0.95
    assert summary["doc_type"] == "invoice"
    assert summary["fields"]["VendorName"]["confidence"] == 0.99
    assert summary["fields"]["Total"]["confidence"] == 0.92
