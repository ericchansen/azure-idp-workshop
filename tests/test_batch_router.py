"""Unit tests for batch processing router and service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from workshop.server import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_batch_empty_samples_returns_400(client: AsyncClient) -> None:
    """Empty sample list returns 400."""
    resp = await client.post("/api/batch/process", json={"samples": []})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_batch_oversize_returns_400(client: AsyncClient) -> None:
    """Batch exceeding MAX_BATCH_SIZE returns 400."""
    samples = [f"doc{i}.pdf" for i in range(25)]
    resp = await client.post("/api/batch/process", json={"samples": samples})
    assert resp.status_code == 400
    assert "exceeds maximum" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_batch_deduplicates_samples(client: AsyncClient) -> None:
    """Duplicate samples are deduplicated before processing."""
    mock_process = AsyncMock(
        return_value={
            "result": {
                "documents": [{"sample": "a.pdf"}],
                "summary": {"total": 1, "succeeded": 1, "failed": 0},
            },
            "trace": {},
        }
    )
    with patch("workshop.routers.batch.batch_service.process_batch", mock_process):
        resp = await client.post(
            "/api/batch/process", json={"samples": ["a.pdf", "a.pdf", "a.pdf"]}
        )
    assert resp.status_code == 200
    mock_process.assert_called_once_with(["a.pdf"])


@pytest.mark.asyncio
async def test_batch_success_returns_per_doc_results(client: AsyncClient) -> None:
    """Successful batch returns per-document results."""
    mock_result = {
        "result": {
            "documents": [
                {"sample": "a.pdf", "document_id": "abc", "cu_fields": {"summary": "test"}},
                {"sample": "b.pdf", "error": "CU failed"},
            ],
            "summary": {
                "total": 2,
                "succeeded": 1,
                "failed": 1,
                "total_cu_ms": 100,
                "total_search_ms": 10,
                "total_ms": 110,
            },
        },
        "trace": {"ensure_index": {}},
    }
    with patch(
        "workshop.routers.batch.batch_service.process_batch",
        AsyncMock(return_value=mock_result),
    ):
        resp = await client.post("/api/batch/process", json={"samples": ["a.pdf", "b.pdf"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["summary"]["succeeded"] == 1
    assert data["result"]["summary"]["failed"] == 1
    assert len(data["result"]["documents"]) == 2


@pytest.mark.asyncio
async def test_batch_service_rounds_cu_duration_on_search_exception() -> None:
    """Search indexing exception path returns rounded CU duration."""
    from workshop.services import batch as batch_service

    with (
        patch("workshop.services.batch.read_sample", return_value=b"bytes"),
        patch(
            "workshop.services.batch.cu_service.analyze_custom",
            AsyncMock(
                return_value={
                    "result": {
                        "fields": {
                            "summary": {"valueString": "Test"},
                            "key_topics": {"valueString": "Topic"},
                        },
                        "content": "body",
                    },
                    "trace": {"duration_ms": 12.3456, "response": {"status": 200}},
                }
            ),
        ),
        patch(
            "workshop.services.batch.ais_service.index_document",
            AsyncMock(side_effect=RuntimeError("search down")),
        ),
    ):
        result = await batch_service._process_single("a.pdf", "analyzer")

    assert result["error"] == "Search indexing failed: search down"
    assert result["cu_duration_ms"] == 12.35
