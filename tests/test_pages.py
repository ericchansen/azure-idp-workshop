"""Page rendering tests."""

from __future__ import annotations


def test_index_page(client):  # type: ignore[no-untyped-def]
    resp = client.get("/")
    assert resp.status_code == 200
    assert "IDP Workshop" in resp.text


def test_module_1_page(client):  # type: ignore[no-untyped-def]
    resp = client.get("/module/1")
    assert resp.status_code == 200
    assert "OCR" in resp.text
    assert "Purchase Order A" in resp.text


def test_module_2_page(client):  # type: ignore[no-untyped-def]
    resp = client.get("/module/2")
    assert resp.status_code == 200
    assert "Unstructured" in resp.text


def test_guide_page(client):  # type: ignore[no-untyped-def]
    resp = client.get("/guide")
    assert resp.status_code == 200
    assert "Decision" in resp.text
