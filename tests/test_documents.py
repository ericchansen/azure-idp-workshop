"""Document listing tests."""

from __future__ import annotations


def test_list_samples(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/documents/samples")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
