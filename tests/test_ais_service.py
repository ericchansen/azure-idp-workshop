"""AI Search service layer tests with mocked Azure SDK."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from azure.core.exceptions import HttpResponseError

from workshop.services.ai_search import (
    ensure_index,
    get_index_stats,
    index_document,
    search_documents,
)

# --- ensure_index ---


@patch("workshop.services.ai_search._get_index_client")
async def test_ensure_index_success(mock_get_client: MagicMock) -> None:
    """Successful index creation returns name + field count."""
    mock_result = MagicMock()
    mock_result.name = "workshop-index"
    mock_result.fields = [MagicMock()] * 7  # 7 fields in schema
    mock_get_client.return_value.create_or_update_index.return_value = mock_result

    result = await ensure_index()

    assert result["result"]["name"] == "workshop-index"
    assert result["result"]["fields"] == 7
    assert result["trace"]["response"]["status"] == 200
    assert result["trace"]["duration_ms"] >= 0


@patch("workshop.services.ai_search._get_index_client")
async def test_ensure_index_sdk_exception(mock_get_client: MagicMock) -> None:
    """Generic SDK exception is caught and wrapped in trace."""
    mock_get_client.return_value.create_or_update_index.side_effect = RuntimeError(
        "Index creation failed"
    )

    result = await ensure_index()

    assert result["result"] == {}
    assert "Index creation failed" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 500


@patch("workshop.services.ai_search._get_index_client")
async def test_ensure_index_http_response_error(mock_get_client: MagicMock) -> None:
    """HttpResponseError preserves the real HTTP status code."""
    mock_get_client.return_value.create_or_update_index.side_effect = HttpResponseError(
        message="Forbidden"
    )
    mock_get_client.return_value.create_or_update_index.side_effect.status_code = 403

    result = await ensure_index()

    assert result["result"] == {}
    assert "HttpResponseError" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 403


# --- index_document ---


@patch("workshop.services.ai_search._get_search_client")
async def test_index_document_success(mock_get_client: MagicMock) -> None:
    """Successful document indexing returns indexed count."""
    mock_upload_result = MagicMock()
    mock_upload_result.succeeded = True
    mock_get_client.return_value.upload_documents.return_value = [mock_upload_result]

    doc = {"id": "abc", "title": "test.pdf", "content": "hello"}
    result = await index_document(doc)

    assert result["result"]["indexed"] == 1
    assert result["result"]["total"] == 1
    assert result["trace"]["response"]["status"] == 200


@patch("workshop.services.ai_search._get_search_client")
async def test_index_document_sdk_exception(mock_get_client: MagicMock) -> None:
    """SDK exception during indexing is caught and traced."""
    mock_get_client.return_value.upload_documents.side_effect = RuntimeError("Upload failed")

    result = await index_document({"id": "abc"})

    assert result["result"] == {}
    assert "Upload failed" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 500


@patch("workshop.services.ai_search._get_search_client")
async def test_index_document_http_response_error(mock_get_client: MagicMock) -> None:
    """HttpResponseError during indexing preserves status code."""
    err = HttpResponseError(message="Service unavailable")
    err.status_code = 503
    mock_get_client.return_value.upload_documents.side_effect = err

    result = await index_document({"id": "abc"})

    assert result["result"] == {}
    assert result["trace"]["response"]["status"] == 503


# --- search_documents ---


@patch("workshop.services.ai_search._get_search_client")
async def test_search_documents_success(mock_get_client: MagicMock) -> None:
    """Successful search returns hits with scores."""
    mock_hit = {
        "id": "doc1",
        "title": "Invoice",
        "summary": "An invoice doc",
        "key_topics": "billing, payment",
        "source_doc": "invoice.pdf",
        "content": "Full content here",
        "@search.score": 0.95,
        "@search.reranker_score": 3.2,
    }
    mock_results = MagicMock()
    mock_results.__iter__ = MagicMock(return_value=iter([mock_hit]))
    mock_results.get_count.return_value = 1
    mock_get_client.return_value.search.return_value = mock_results

    result = await search_documents("invoice", top=5)

    assert result["trace"]["response"]["status"] == 200
    assert len(result["result"]["hits"]) == 1
    assert result["result"]["hits"][0]["title"] == "Invoice"
    assert result["result"]["hits"][0]["key_topics"] == "billing, payment"
    assert result["result"]["hits"][0]["score"] == 0.95
    assert result["result"]["total"] == 1


@patch("workshop.services.ai_search._get_search_client")
async def test_search_documents_no_count_fallback(mock_get_client: MagicMock) -> None:
    """When get_count() returns None, falls back to len(hits)."""
    mock_hit = {"id": "1", "title": "doc", "content": "text"}
    mock_results = MagicMock()
    mock_results.__iter__ = MagicMock(return_value=iter([mock_hit]))
    mock_results.get_count.return_value = None
    mock_get_client.return_value.search.return_value = mock_results

    result = await search_documents("test")

    assert result["result"]["total"] == 1  # falls back to len(hits)


@patch("workshop.services.ai_search._get_search_client")
async def test_search_documents_sdk_exception(mock_get_client: MagicMock) -> None:
    """SDK exception during search is caught and traced."""
    mock_get_client.return_value.search.side_effect = RuntimeError("Search failed")

    result = await search_documents("test")

    assert result["result"]["hits"] == []
    assert result["result"]["total"] == 0
    assert "Search failed" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 500


@patch("workshop.services.ai_search._get_search_client")
async def test_search_documents_http_response_error(mock_get_client: MagicMock) -> None:
    """HttpResponseError during search preserves status code."""
    err = HttpResponseError(message="Rate limited")
    err.status_code = 429
    mock_get_client.return_value.search.side_effect = err

    result = await search_documents("test")

    assert result["result"]["hits"] == []
    assert result["trace"]["response"]["status"] == 429


# --- get_index_stats ---


@patch("workshop.services.ai_search._get_index_client")
async def test_get_index_stats_success(mock_get_client: MagicMock) -> None:
    """Successful stats returns document count and storage size."""
    mock_stats = MagicMock()
    mock_stats.document_count = 42
    mock_stats.storage_size = 1024000
    mock_get_client.return_value.get_index_statistics.return_value = mock_stats

    result = await get_index_stats()

    assert result["result"]["document_count"] == 42
    assert result["result"]["storage_size"] == 1024000
    assert result["trace"]["response"]["status"] == 200


@patch("workshop.services.ai_search._get_index_client")
async def test_get_index_stats_sdk_exception(mock_get_client: MagicMock) -> None:
    """SDK exception during stats is caught and traced."""
    mock_get_client.return_value.get_index_statistics.side_effect = RuntimeError("Stats failed")

    result = await get_index_stats()

    assert result["result"]["document_count"] == 0
    assert result["result"]["storage_size"] == 0
    assert "Stats failed" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 500


@patch("workshop.services.ai_search._get_index_client")
async def test_get_index_stats_http_response_error(mock_get_client: MagicMock) -> None:
    """HttpResponseError during stats preserves status code."""
    err = HttpResponseError(message="Not found")
    err.status_code = 404
    mock_get_client.return_value.get_index_statistics.side_effect = err

    result = await get_index_stats()

    assert result["result"]["document_count"] == 0
    assert result["trace"]["response"]["status"] == 404
