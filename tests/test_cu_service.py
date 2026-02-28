"""CU service layer tests with mocked Azure SDK."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from workshop.services.content_understanding import (
    _result_to_dict,
    _summarize_cu_result,
    analyze_custom,
    analyze_layout,
    analyze_prebuilt,
)


@patch("workshop.services.content_understanding._get_client")
def test_analyze_layout_success(mock_get_client: MagicMock) -> None:
    """Successful CU layout analysis returns result + trace."""
    mock_result = MagicMock()
    mock_result.as_dict.return_value = {
        "contents": [{"markdown": "# Hello\n\nWorld"}],
    }
    mock_poller = MagicMock()
    mock_poller.result.return_value = mock_result
    mock_get_client.return_value.begin_analyze_binary.return_value = mock_poller

    result = analyze_layout(b"fake-bytes", "test.png")

    assert "result" in result
    assert "trace" in result
    assert result["trace"]["response"]["status"] == 200
    assert result["trace"]["duration_ms"] >= 0


@patch("workshop.services.content_understanding._get_client")
def test_analyze_layout_sdk_exception(mock_get_client: MagicMock) -> None:
    """SDK exception is caught and wrapped in trace."""
    mock_get_client.return_value.begin_analyze_binary.side_effect = RuntimeError(
        "CU service exploded"
    )

    result = analyze_layout(b"fake-bytes", "test.png")

    assert result["result"] == {}
    assert "CU service exploded" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 500


@patch("workshop.services.content_understanding._get_client")
def test_analyze_layout_content_empty_exception(mock_get_client: MagicMock) -> None:
    """ContentEmpty exception from CU SDK is caught gracefully."""
    mock_get_client.return_value.begin_analyze_binary.side_effect = Exception(
        "(InvalidRequest) Invalid request. Code: InvalidRequest. "
        'Inner error: { "code": "ContentEmpty", '
        '"message": "No fields were extracted because the content is empty." }'
    )

    result = analyze_layout(b"fake-bytes", "receipt.png")

    assert result["result"] == {}
    assert "ContentEmpty" in result["trace"]["error"]
    assert result["trace"]["response"]["status"] == 500


@patch("workshop.services.content_understanding._get_client")
def test_analyze_prebuilt_success(mock_get_client: MagicMock) -> None:
    """Successful prebuilt analysis returns fields."""
    mock_result = MagicMock()
    mock_result.as_dict.return_value = {
        "contents": [
            {
                "markdown": "Invoice text",
                "fields": {
                    "VendorName": {"value": "Contoso", "confidence": 0.93},
                },
            }
        ],
    }
    mock_poller = MagicMock()
    mock_poller.result.return_value = mock_result
    mock_get_client.return_value.begin_analyze_binary.return_value = mock_poller

    result = analyze_prebuilt("prebuilt-invoice", b"bytes", "invoice.pdf")

    assert result["trace"]["response"]["status"] == 200
    assert "result" in result


@patch("workshop.services.content_understanding._get_client")
def test_analyze_custom_success(mock_get_client: MagicMock) -> None:
    """Successful custom analysis with field definitions."""
    mock_client = mock_get_client.return_value
    # get_analyzer succeeds (analyzer exists)
    mock_client.get_analyzer.return_value = MagicMock()

    mock_result = MagicMock()
    mock_result.as_dict.return_value = {
        "contents": [
            {
                "fields": {
                    "summary": {"value": "A contract summary", "confidence": 0.88},
                    "risk_level": {"value": "Medium", "confidence": 0.82},
                },
            }
        ],
    }
    mock_poller = MagicMock()
    mock_poller.result.return_value = mock_result
    mock_client.begin_analyze_binary.return_value = mock_poller

    fields = [
        {"name": "summary", "type": "string", "description": "Summary"},
        {"name": "risk_level", "type": "string", "description": "Risk level"},
    ]
    result = analyze_custom("workshopContract", b"bytes", "contract.txt", fields)

    assert result["trace"]["response"]["status"] == 200


@patch("workshop.services.content_understanding._get_client")
def test_analyze_custom_creates_analyzer(mock_get_client: MagicMock) -> None:
    """Custom analysis creates analyzer if it doesn't exist."""
    mock_client = mock_get_client.return_value
    # get_analyzer fails (doesn't exist)
    mock_client.get_analyzer.side_effect = Exception("Not found")
    # begin_create_analyzer succeeds
    mock_create_poller = MagicMock()
    mock_client.begin_create_analyzer.return_value = mock_create_poller

    mock_result = MagicMock()
    mock_result.as_dict.return_value = {"contents": []}
    mock_analyze_poller = MagicMock()
    mock_analyze_poller.result.return_value = mock_result
    mock_client.begin_analyze_binary.return_value = mock_analyze_poller

    result = analyze_custom("new-analyzer", b"bytes", "doc.txt", None)

    mock_client.begin_create_analyzer.assert_called_once()
    assert result["trace"]["response"]["status"] == 200


@patch("workshop.services.content_understanding._get_client")
def test_analyze_custom_exception(mock_get_client: MagicMock) -> None:
    """Custom analysis exception is caught."""
    mock_client = mock_get_client.return_value
    mock_client.get_analyzer.return_value = MagicMock()
    mock_client.begin_analyze_binary.side_effect = Exception("Custom analyzer failed")

    result = analyze_custom("workshopContract", b"bytes", "doc.txt", None)

    assert result["result"] == {}
    assert "Custom analyzer failed" in result["trace"]["error"]


def test_result_to_dict_synthesizes_content() -> None:
    """_result_to_dict creates top-level content from contents[].markdown."""
    mock_obj = MagicMock()
    mock_obj.as_dict.return_value = {
        "contents": [
            {"markdown": "# Hello"},
            {"markdown": "World"},
        ],
    }
    result = _result_to_dict(mock_obj)
    assert result["content"] == "# Hello\n\nWorld"


def test_result_to_dict_lifts_fields() -> None:
    """_result_to_dict lifts fields from first content item."""
    mock_obj = MagicMock()
    mock_obj.as_dict.return_value = {
        "contents": [
            {
                "fields": {
                    "summary": {"value": "test", "confidence": 0.9},
                },
            }
        ],
    }
    result = _result_to_dict(mock_obj)
    assert "summary" in result["fields"]


def test_result_to_dict_fallback() -> None:
    """_result_to_dict falls back on error."""

    class BadResult:
        def as_dict(self) -> None:
            raise Exception("broken")

        def __repr__(self) -> str:
            return "BadResult()"

    result = _result_to_dict(BadResult())
    assert "raw" in result
    assert "BadResult" in result["raw"]


def test_summarize_cu_result_with_content() -> None:
    """_summarize_cu_result creates content preview."""
    result = {"content": "Hello " * 200, "contents": [{}, {}]}
    summary = _summarize_cu_result(result)
    assert "content_preview" in summary
    assert summary["content_count"] == 2


def test_summarize_cu_result_with_fields() -> None:
    """_summarize_cu_result extracts field summaries."""
    result = {
        "fields": {
            "summary": {"value": "A summary", "confidence": 0.88},
        }
    }
    summary = _summarize_cu_result(result)
    assert "summary" in summary["fields"]
    assert summary["fields"]["summary"]["confidence"] == 0.88


def test_summarize_cu_result_empty() -> None:
    """_summarize_cu_result handles empty result."""
    summary = _summarize_cu_result({})
    assert summary == {}


def test_result_to_dict_lifts_usage() -> None:
    """_result_to_dict lifts usage data from contents to top level."""
    mock_obj = MagicMock()
    mock_obj.as_dict.return_value = {
        "contents": [
            {
                "markdown": "Some text",
                "usage": {"promptTokens": 150, "completionTokens": 50},
            }
        ],
    }
    result = _result_to_dict(mock_obj)
    assert "usage" in result
    assert result["usage"]["promptTokens"] == 150
    assert result["usage"]["completionTokens"] == 50


def test_result_to_dict_preserves_top_level_usage() -> None:
    """_result_to_dict does not overwrite existing top-level usage."""
    mock_obj = MagicMock()
    mock_obj.as_dict.return_value = {
        "usage": {"promptTokens": 200, "completionTokens": 100},
        "contents": [
            {"usage": {"promptTokens": 10, "completionTokens": 5}},
        ],
    }
    result = _result_to_dict(mock_obj)
    assert result["usage"]["promptTokens"] == 200


def test_summarize_cu_result_with_usage() -> None:
    """_summarize_cu_result includes usage/token data in summary."""
    result = {
        "usage": {"promptTokens": 150, "completionTokens": 50},
    }
    summary = _summarize_cu_result(result)
    assert "usage" in summary
    assert summary["usage"]["promptTokens"] == 150
