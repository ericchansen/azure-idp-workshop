"""Azure AI Search service — index and search documents."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from workshop.config import settings
from workshop.services.api_trace import ApiTrace, TraceTimer, sanitize_headers

logger = logging.getLogger(__name__)

# Index field schema — documents enriched by CU
INDEX_FIELDS = [
    {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
    {"name": "title", "type": "Edm.String", "searchable": True},
    {"name": "content", "type": "Edm.String", "searchable": True},
    {"name": "summary", "type": "Edm.String", "searchable": True},
    {"name": "source_doc", "type": "Edm.String", "filterable": True},
    {"name": "indexed_at", "type": "Edm.DateTimeOffset", "filterable": True, "sortable": True},
]


def _get_credential() -> Any:
    """Return AzureKeyCredential if key set, else DefaultAzureCredential."""
    if settings.ais_key:
        from azure.core.credentials import AzureKeyCredential

        return AzureKeyCredential(settings.ais_key)
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def _get_search_client() -> Any:
    """Lazy-initialize the AI Search query client."""
    from azure.search.documents import SearchClient

    if not settings.ais_endpoint:
        raise RuntimeError("AIS_ENDPOINT not configured")
    return SearchClient(
        endpoint=settings.ais_endpoint,
        index_name=settings.ais_index_name,
        credential=_get_credential(),
    )


def _get_index_client() -> Any:
    """Lazy-initialize the AI Search index management client."""
    from azure.search.documents.indexes import SearchIndexClient

    if not settings.ais_endpoint:
        raise RuntimeError("AIS_ENDPOINT not configured")
    return SearchIndexClient(
        endpoint=settings.ais_endpoint,
        credential=_get_credential(),
    )


async def ensure_index() -> dict[str, Any]:
    """Create the search index if it doesn't exist. Returns index info + trace."""
    trace = ApiTrace(service="AI-Search", operation="ensure-index")
    trace.request_url = f"{settings.ais_endpoint}/indexes/{settings.ais_index_name}"
    trace.request_method = "PUT"
    trace.request_headers = sanitize_headers({"Content-Type": "application/json"})

    with TraceTimer() as timer:
        try:
            from azure.search.documents.indexes.models import (
                SearchableField,
                SearchFieldDataType,
                SearchIndex,
                SemanticConfiguration,
                SemanticField,
                SemanticPrioritizedFields,
                SemanticSearch,
                SimpleField,
            )

            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
                SearchableField(name="title", type=SearchFieldDataType.String),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SearchableField(name="summary", type=SearchFieldDataType.String),
                SimpleField(name="source_doc", type=SearchFieldDataType.String, filterable=True),
                SimpleField(
                    name="indexed_at",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
            ]

            semantic_config = SemanticConfiguration(
                name="default",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="content")],
                    title_field=SemanticField(field_name="title"),
                    keywords_fields=[SemanticField(field_name="summary")],
                ),
            )

            index = SearchIndex(
                name=settings.ais_index_name,
                fields=fields,
                semantic_search=SemanticSearch(configurations=[semantic_config]),
            )

            client = _get_index_client()
            result = await asyncio.to_thread(client.create_or_update_index, index)
            trace.response_status = 200
            result_dict = {"name": result.name, "fields": len(result.fields)}
        except Exception as e:
            trace.error = f"{type(e).__name__}: {e}"
            trace.response_status = 500
            result_dict = {}

    trace.duration_ms = timer.elapsed_ms
    return {"result": result_dict, "trace": trace.to_dict()}


async def index_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Push a single document to the search index. Returns result + trace."""
    trace = ApiTrace(service="AI-Search", operation="index-document")
    trace.request_url = f"{settings.ais_endpoint}/indexes/{settings.ais_index_name}/docs/index"
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/json"})
    trace.request_body = {"id": doc.get("id"), "title": doc.get("title", "")[:100]}

    with TraceTimer() as timer:
        try:
            client = _get_search_client()
            result = await asyncio.to_thread(client.upload_documents, documents=[doc])
            succeeded = sum(1 for r in result if r.succeeded)
            trace.response_status = 200
            result_dict = {"indexed": succeeded, "total": len(result)}
        except Exception as e:
            trace.error = f"{type(e).__name__}: {e}"
            trace.response_status = 500
            result_dict = {}

    trace.duration_ms = timer.elapsed_ms
    return {"result": result_dict, "trace": trace.to_dict()}


async def search_documents(query: str, top: int = 5, use_semantic: bool = True) -> dict[str, Any]:
    """Search the index. Returns results + trace."""
    trace = ApiTrace(service="AI-Search", operation="search")
    trace.request_url = f"{settings.ais_endpoint}/indexes/{settings.ais_index_name}/docs/search"
    trace.request_method = "POST"
    trace.request_headers = sanitize_headers({"Content-Type": "application/json"})
    trace.request_body = {
        "search": query,
        "top": top,
        "queryType": "semantic" if use_semantic else "simple",
    }

    with TraceTimer() as timer:
        try:
            client = _get_search_client()

            search_kwargs: dict[str, Any] = {
                "search_text": query,
                "top": top,
                "include_total_count": True,
            }
            if use_semantic:
                search_kwargs["query_type"] = "semantic"
                search_kwargs["semantic_configuration_name"] = "default"

            def _run_search() -> Any:
                return client.search(**search_kwargs)

            results = await asyncio.to_thread(_run_search)

            hits = []
            total = 0
            for r in results:
                total += 1
                hits.append(
                    {
                        "id": r.get("id"),
                        "title": r.get("title", ""),
                        "summary": r.get("summary", ""),
                        "source_doc": r.get("source_doc", ""),
                        "score": r.get("@search.score"),
                        "reranker_score": r.get("@search.reranker_score"),
                        "content_preview": (r.get("content") or "")[:300],
                    }
                )
            trace.response_status = 200
            result_dict = {"hits": hits, "total": total, "query": query}
        except Exception as e:
            trace.error = f"{type(e).__name__}: {e}"
            trace.response_status = 500
            result_dict = {"hits": [], "total": 0, "query": query}

    trace.duration_ms = timer.elapsed_ms
    return {"result": result_dict, "trace": trace.to_dict()}


async def get_index_stats() -> dict[str, Any]:
    """Get index document count and status."""
    trace = ApiTrace(service="AI-Search", operation="index-stats")
    trace.request_url = f"{settings.ais_endpoint}/indexes/{settings.ais_index_name}/stats"
    trace.request_method = "GET"

    with TraceTimer() as timer:
        try:
            client = _get_index_client()
            stats = await asyncio.to_thread(client.get_index_statistics, settings.ais_index_name)
            trace.response_status = 200
            result_dict = {
                "document_count": stats.document_count,
                "storage_size": stats.storage_size,
            }
        except Exception as e:
            trace.error = f"{type(e).__name__}: {e}"
            trace.response_status = 500
            result_dict = {"document_count": 0, "storage_size": 0}

    trace.duration_ms = timer.elapsed_ms
    return {"result": result_dict, "trace": trace.to_dict()}
