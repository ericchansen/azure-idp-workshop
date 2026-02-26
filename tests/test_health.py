"""Health endpoint tests."""

from __future__ import annotations


def test_health_returns_ok(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_health_includes_environment(client):  # type: ignore[no-untyped-def]
    resp = client.get("/api/health")
    data = resp.json()
    assert "environment" in data
