"""Document listing tests."""

from __future__ import annotations


def test_list_samples(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/documents/samples")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_sample_raw_png(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/documents/samples/receipt.png/raw")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 0


def test_get_sample_raw_pdf(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/documents/samples/invoice.pdf/raw")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_get_sample_raw_not_found(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/documents/samples/nonexistent.xyz/raw")
    assert resp.status_code == 404
