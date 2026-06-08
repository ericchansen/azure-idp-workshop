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


def test_get_sample_raw_contract_pdf(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/documents/samples/contract.pdf/raw")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 0


def test_upload_document_returns_metadata(client):  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("upload.pdf", b"%PDF-1.4\n", "application/pdf")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "upload.pdf"
    assert data["size_bytes"] == 9
    assert data["content_type"] == "application/pdf"
    assert data["source_type"] == "upload"


def test_upload_document_rejects_unsupported_extension(client):  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert "does not support" in resp.json()["detail"]


def test_upload_document_rejects_oversized_file(client):  # type: ignore[no-untyped-def]
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("large.pdf", b"x" * (10 * 1024 * 1024 + 1), "application/pdf")},
    )
    assert resp.status_code == 413
    assert "maximum upload size" in resp.json()["detail"]
