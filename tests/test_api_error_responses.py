"""Tests verifying all API endpoints return valid JSON on errors."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from workshop.server import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestDIEndpointsReturnJSON:
    """DI endpoints must always return valid JSON, even on errors."""

    @pytest.mark.asyncio
    async def test_di_layout_missing_sample_returns_json(self, client):
        resp = await client.post("/api/di/layout")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert "detail" in data or "error" in data or "result" in data

    @pytest.mark.asyncio
    async def test_di_layout_nonexistent_sample_returns_json(self, client):
        resp = await client.post("/api/di/layout?sample=nonexistent.xyz")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_di_prebuilt_invalid_model_returns_json(self, client):
        resp = await client.post("/api/di/prebuilt/invalid-model?sample=invoice.pdf")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_di_prebuilt_missing_sample_returns_json(self, client):
        resp = await client.post("/api/di/prebuilt/prebuilt-invoice")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)


class TestCUEndpointsReturnJSON:
    """CU endpoints must always return valid JSON, even on errors."""

    @pytest.mark.asyncio
    async def test_cu_layout_missing_sample_returns_json(self, client):
        resp = await client.post("/api/cu/layout")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert "detail" in data or "error" in data or "result" in data

    @pytest.mark.asyncio
    async def test_cu_layout_nonexistent_sample_returns_json(self, client):
        resp = await client.post("/api/cu/layout?sample=nonexistent.xyz")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_cu_prebuilt_invalid_model_returns_json(self, client):
        resp = await client.post("/api/cu/prebuilt/invalid-model?sample=invoice.pdf")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_cu_prebuilt_missing_sample_returns_json(self, client):
        resp = await client.post("/api/cu/prebuilt/prebuilt-invoice")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_cu_custom_empty_body_returns_json(self, client):
        resp = await client.post("/api/cu/custom")
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_cu_custom_invalid_body_returns_json(self, client):
        resp = await client.post(
            "/api/cu/custom",
            content="not json",
            headers={"content-type": "application/json"},
        )
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert isinstance(data, dict)


class TestResponsesAreValidJSON:
    """All responses must be parseable as JSON (no plain text errors)."""

    ENDPOINTS = [
        ("POST", "/api/di/layout"),
        ("POST", "/api/cu/layout"),
        ("POST", "/api/di/prebuilt/prebuilt-invoice"),
        ("POST", "/api/cu/prebuilt/prebuilt-invoice"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,url", ENDPOINTS)
    async def test_response_is_valid_json(self, client, method, url):
        resp = await client.request(method, url)
        try:
            resp.json()
        except json.JSONDecodeError:
            pytest.fail(f"{method} {url} returned non-JSON: {resp.text[:200]}")
