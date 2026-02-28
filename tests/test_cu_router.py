"""CU router tests (mocked — no real Azure calls)."""

from __future__ import annotations


def test_cu_layout_requires_file_or_sample(client):  # type: ignore[no-untyped-def]
    resp = client.post("/api/cu/layout")
    assert resp.status_code == 400


def test_cu_prebuilt_rejects_unknown_model(client):  # type: ignore[no-untyped-def]
    resp = client.post("/api/cu/prebuilt/unknown-analyzer")
    assert resp.status_code == 400


def test_cu_prebuilt_accepts_valid_names(client):  # type: ignore[no-untyped-def]
    valid = ["prebuilt-invoice", "prebuilt-receipt", "prebuilt-read", "prebuilt-layout"]
    for name in valid:
        resp = client.post(f"/api/cu/prebuilt/{name}")
        assert resp.status_code == 400
        assert "Provide" in resp.json()["detail"]


def test_cu_custom_accepts_json_body_with_sample(client):  # type: ignore[no-untyped-def]
    """CU custom endpoint parses JSON body correctly (sample found, may fail on Azure)."""
    import pytest

    # The endpoint will accept the JSON body and find the sample file,
    # then fail with RuntimeError because Azure isn't configured in tests.
    # That RuntimeError proves we got PAST the request parsing + sample lookup.
    with pytest.raises(RuntimeError, match="AI_SERVICES_ENDPOINT"):
        client.post(
            "/api/cu/custom",
            json={
                "sample": "contract.pdf",
                "fields": [{"name": "summary", "type": "string", "description": "A summary"}],
                "analyzer_id": "workshopContract",
            },
        )


def test_cu_custom_rejects_empty_body(client):  # type: ignore[no-untyped-def]
    """CU custom returns 400 when no sample is provided in JSON body."""
    resp = client.post(
        "/api/cu/custom",
        json={"analyzer_id": "test"},
    )
    assert resp.status_code == 400
    assert "sample" in resp.json()["detail"].lower()


def test_cu_custom_nonexistent_sample_returns_404(client):  # type: ignore[no-untyped-def]
    """CU custom returns 404 for nonexistent sample file."""
    resp = client.post(
        "/api/cu/custom",
        json={"sample": "nonexistent.xyz"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
