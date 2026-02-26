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
