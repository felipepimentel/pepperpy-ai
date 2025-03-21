"""Tests for HTTP utility functions."""

import pytest

from pepperpy.http.errors import ResponseError
from pepperpy.http.helpers import (
    check_status_code,
    format_headers,
    get_content_type,
    is_json_content,
    parse_json,
    parse_query_params,
)


def test_parse_json():
    """Test JSON parsing functionality."""
    # Test valid JSON string
    content = '{"key": "value"}'
    result = parse_json(content)
    assert isinstance(result, dict)
    assert result["key"] == "value"

    # Test valid JSON bytes
    content_bytes = b'{"key": "value"}'
    result = parse_json(content_bytes)
    assert isinstance(result, dict)
    assert result["key"] == "value"

    # Test invalid JSON
    with pytest.raises(ResponseError) as exc_info:
        parse_json("{invalid json}")
    assert "Failed to parse content as JSON" in str(exc_info.value)

    # Test with status code
    with pytest.raises(ResponseError) as exc_info:
        parse_json("{invalid json}", status_code=400)
    assert exc_info.value.status_code == 400


def test_check_status_code():
    """Test status code validation."""
    # Test successful status codes
    for code in [200, 201, 204, 301, 302]:
        check_status_code(code)  # Should not raise

    # Test client errors
    for code in [400, 401, 403, 404, 422]:
        with pytest.raises(ResponseError) as exc_info:
            check_status_code(code)
        assert "Client error" in str(exc_info.value)
        assert exc_info.value.status_code == code

    # Test server errors
    for code in [500, 501, 502, 503, 504]:
        with pytest.raises(ResponseError) as exc_info:
            check_status_code(code)
        assert "Server error" in str(exc_info.value)
        assert exc_info.value.status_code == code


def test_get_content_type():
    """Test content type extraction from headers."""
    # Test simple content type
    headers = {"content-type": "application/json"}
    assert get_content_type(headers) == "application/json"

    # Test content type with charset
    headers = {"content-type": "application/json; charset=utf-8"}
    assert get_content_type(headers) == "application/json"

    # Test content type with parameters
    headers = {"content-type": "text/html; charset=utf-8; boundary=something"}
    assert get_content_type(headers) == "text/html"

    # Test missing content type
    headers = {}
    assert get_content_type(headers) == ""

    # Test case insensitivity
    headers = {"Content-Type": "APPLICATION/JSON"}
    assert get_content_type(headers) == "application/json"


def test_is_json_content():
    """Test JSON content type detection."""
    # Test application/json
    headers = {"content-type": "application/json"}
    assert is_json_content(headers) is True

    # Test text/json
    headers = {"content-type": "text/json"}
    assert is_json_content(headers) is True

    # Test with charset
    headers = {"content-type": "application/json; charset=utf-8"}
    assert is_json_content(headers) is True

    # Test non-JSON content types
    for content_type in ["text/plain", "text/html", "application/xml"]:
        headers = {"content-type": content_type}
        assert is_json_content(headers) is False

    # Test missing content type
    headers = {}
    assert is_json_content(headers) is False


def test_format_headers():
    """Test header formatting."""
    # Test mixed case headers
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "test-key",
        "accept": "application/json",
    }
    formatted = format_headers(headers)
    assert all(k.islower() for k in formatted.keys())
    assert formatted["content-type"] == "application/json"
    assert formatted["x-api-key"] == "test-key"
    assert formatted["accept"] == "application/json"

    # Test empty headers
    assert format_headers({}) == {}

    # Test already lowercase headers
    headers = {"content-type": "application/json"}
    assert format_headers(headers) == headers


def test_parse_query_params():
    """Test query parameter parsing."""
    # Test simple parameters
    query = "key1=value1&key2=value2"
    params = parse_query_params(query)
    assert params == {"key1": "value1", "key2": "value2"}

    # Test empty value
    query = "key1=&key2=value2"
    params = parse_query_params(query)
    assert params == {"key1": "", "key2": "value2"}

    # Test parameter without value
    query = "key1&key2=value2"
    params = parse_query_params(query)
    assert params == {"key1": "", "key2": "value2"}

    # Test empty query string
    assert parse_query_params("") == {}

    # Test multiple values for same key (last one wins)
    query = "key=value1&key=value2"
    params = parse_query_params(query)
    assert params == {"key": "value2"}

    # Test special characters
    query = "key1=hello%20world&key2=test%21"
    params = parse_query_params(query)
    assert params == {"key1": "hello%20world", "key2": "test%21"}
