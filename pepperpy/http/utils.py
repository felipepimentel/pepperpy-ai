"""Utility functions for HTTP module.

This module provides utility functions for HTTP client and server components,
including JSON parsing, header manipulation, content type detection, and
status code validation.
"""

import json
from typing import Any, Dict, Optional, Union

from pepperpy.http.errors import ResponseError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


def parse_json(content: Union[str, bytes], status_code: Optional[int] = None) -> Any:
    """Parse JSON content from string or bytes.

    Safely converts the provided content to a Python object by parsing it as JSON.
    Handles both string and bytes input formats, with automatic UTF-8 decoding
    for bytes content.

    Args:
        content: The JSON content to parse, either as a string or bytes
        status_code: Optional HTTP status code for error context

    Returns:
        Any: The parsed JSON content as Python objects (dict, list, etc.)

    Raises:
        ResponseError: If the content cannot be parsed as valid JSON

    Example:
        >>> response_body = '{"status": "success", "data": [1, 2, 3]}'
        >>> result = parse_json(response_body)
        >>> assert result["status"] == "success"
        >>> assert result["data"] == [1, 2, 3]
    """
    try:
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse content as JSON: {e}"
        logger.error(error_msg)
        raise ResponseError(error_msg, status_code=status_code)


def check_status_code(status_code: int) -> None:
    """Validate HTTP status code and raise appropriate errors.

    Checks if the provided HTTP status code indicates an error condition
    and raises an appropriate exception if it does. Status codes in the
    4xx range indicate client errors, while codes in the 5xx range
    indicate server errors.

    Args:
        status_code: The HTTP status code to check

    Raises:
        ResponseError: If the status code indicates a client or server error

    Example:
        >>> try:
        ...     check_status_code(200)  # OK, no exception
        ...     check_status_code(404)  # Will raise ResponseError
        ... except ResponseError as e:
        ...     assert e.status_code == 404
        ...     assert "Client error" in str(e)
    """
    if 400 <= status_code < 500:
        raise ResponseError(f"Client error: {status_code}", status_code=status_code)
    elif 500 <= status_code < 600:
        raise ResponseError(f"Server error: {status_code}", status_code=status_code)


def get_content_type(headers: Dict[str, str]) -> str:
    """Extract and normalize content type from HTTP headers.

    Retrieves the Content-Type header value from the provided headers dictionary,
    handling case-insensitivity and parameter stripping (e.g., removing charset).
    Returns an empty string if no Content-Type header is present.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        str: The normalized content type in lowercase, without parameters

    Example:
        >>> headers = {"Content-Type": "application/json; charset=utf-8"}
        >>> content_type = get_content_type(headers)
        >>> assert content_type == "application/json"

        >>> headers = {"content-type": "TEXT/HTML"}
        >>> content_type = get_content_type(headers)
        >>> assert content_type == "text/html"
    """
    # Convert headers to lowercase for case-insensitive comparison
    headers = {k.lower(): v for k, v in headers.items()}
    content_type = headers.get("content-type", "")
    if ";" in content_type:
        content_type = content_type.split(";")[0].strip()
    return content_type.lower()


def is_json_content(headers: Dict[str, str]) -> bool:
    """Determine if the content type in headers indicates JSON.

    Checks if the Content-Type header value indicates JSON content,
    supporting both 'application/json' and 'text/json' MIME types.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        bool: True if the content type indicates JSON, False otherwise

    Example:
        >>> headers = {"Content-Type": "application/json"}
        >>> assert is_json_content(headers) == True

        >>> headers = {"Content-Type": "text/html"}
        >>> assert is_json_content(headers) == False
    """
    content_type = get_content_type(headers)
    return content_type in ("application/json", "text/json")


def format_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Normalize HTTP headers to ensure consistent casing.

    Converts all header names to lowercase for consistent access
    and comparison, while preserving the original header values.

    Args:
        headers: Dictionary of HTTP headers with mixed case

    Returns:
        Dict[str, str]: Dictionary with normalized lowercase header names

    Example:
        >>> headers = {"Content-Type": "application/json", "X-API-KEY": "abc123"}
        >>> normalized = format_headers(headers)
        >>> assert "content-type" in normalized
        >>> assert normalized["content-type"] == "application/json"
        >>> assert normalized["x-api-key"] == "abc123"
    """
    return {k.lower(): v for k, v in headers.items()}


def parse_query_params(query_string: str) -> Dict[str, str]:
    """Parse URL query parameters into a dictionary.

    Converts a URL query string (the part after '?' in a URL) into a
    dictionary of parameter names and values. Handles URL-encoded values
    but does not support multi-value parameters.

    Args:
        query_string: URL query string (without the leading '?')

    Returns:
        Dict[str, str]: Dictionary of query parameters

    Example:
        >>> params = parse_query_params("name=John&age=30")
        >>> assert params == {"name": "John", "age": "30"}

        >>> params = parse_query_params("")
        >>> assert params == {}
    """
    if not query_string:
        return {}

    params = {}
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value
        else:
            params[param] = ""

    return params
