"""AI Search router tests (mocked — no real Azure calls)."""

from __future__ import annotations

import pytest


def test_search_query_empty_string_rejected(client):  # type: ignore[no-untyped-def]
    """POST /api/search/query with empty query returns 400."""
    resp = client.post("/api/search/query", json={"query": "   "})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_search_query_missing_query_returns_422(client):  # type: ignore[no-untyped-def]
    """POST /api/search/query with missing 'query' returns 422."""
    resp = client.post("/api/search/query", json={})
    assert resp.status_code == 422


def test_index_missing_sample_returns_422(client):  # type: ignore[no-untyped-def]
    """POST /api/search/index with no sample returns 422."""
    resp = client.post("/api/search/index", json={})
    assert resp.status_code == 422


def test_index_nonexistent_sample_returns_404(client):  # type: ignore[no-untyped-def]
    """POST /api/search/index with nonexistent sample returns 404."""
    resp = client.post("/api/search/index", json={"sample": "nonexistent.xyz"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_index_valid_sample_reaches_azure(client):  # type: ignore[no-untyped-def]
    """POST /api/search/index with valid sample passes validation and hits Azure."""
    # The endpoint will accept the JSON body and find the sample file,
    # then fail with RuntimeError because Azure isn't configured in tests.
    # That RuntimeError proves we got PAST request parsing + sample lookup.
    with pytest.raises(RuntimeError, match="AI_SERVICES_ENDPOINT"):
        client.post(
            "/api/search/index",
            json={"sample": "contract.pdf"},
        )


def test_index_custom_fields_validated(client):  # type: ignore[no-untyped-def]
    """POST /api/search/index with invalid field structure returns 422."""
    resp = client.post(
        "/api/search/index",
        json={
            "sample": "contract.pdf",
            "fields": [{"invalid_key": "no name field"}],
        },
    )
    assert resp.status_code == 422


def test_index_with_custom_fields_reaches_azure(client):  # type: ignore[no-untyped-def]
    """POST /api/search/index with valid custom fields passes validation."""
    with pytest.raises(RuntimeError, match="AI_SERVICES_ENDPOINT"):
        client.post(
            "/api/search/index",
            json={
                "sample": "contract.pdf",
                "fields": [
                    {"name": "parties", "type": "string", "description": "Contract parties"},
                    {"name": "dates", "type": "string", "description": "Key dates"},
                ],
            },
        )


def test_ensure_index_returns_error_trace(client):  # type: ignore[no-untyped-def]
    """POST /api/search/ensure-index returns error trace when Azure isn't configured."""
    resp = client.post("/api/search/ensure-index")
    # Service catches the exception internally and returns error in trace
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace"]["error"] != ""
    assert data["result"] == {}


def test_stats_returns_error_trace(client):  # type: ignore[no-untyped-def]
    """GET /api/search/stats returns error trace when Azure isn't configured."""
    resp = client.get("/api/search/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace"]["error"] != ""
    assert data["result"]["document_count"] == 0


def test_extract_field_helper() -> None:
    """_extract_field correctly extracts from CU field dicts."""
    from workshop.routers.ais import _extract_field

    # valueString format
    assert _extract_field({"summary": {"valueString": "A summary"}}, "summary") == "A summary"

    # value format
    assert _extract_field({"title": {"value": "Hello"}}, "title") == "Hello"

    # content format
    assert _extract_field({"note": {"content": "Note text"}}, "note") == "Note text"

    # missing field
    assert _extract_field({}, "missing") == ""

    # non-dict field
    assert _extract_field({"count": 42}, "count") == "42"

    # None field
    assert _extract_field({"empty": None}, "empty") == ""
