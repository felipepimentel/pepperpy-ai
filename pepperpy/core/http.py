"""HTTP utilities for PepperPy.

This module provides HTTP client functionality and utilities for the PepperPy framework,
including a client, error handling, and helper functions.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import aiohttp

from pepperpy.core.base import (
    ConfigType,
    HeadersType,
    QueryParamsType,
    JsonType,
    HTTPError,
    RequestError,
    ResponseError,
    ConnectionError,
    TimeoutError,
)

# Helper functions
def parse_json(content: str) -> JsonType:
    """Parse JSON string.

    Args:
        content: JSON string

    Returns:
        Parsed JSON object

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

def check_status_code(
    status_code: int,
    content: Optional[str] = None,
    expected_codes: tuple[int, ...] = (200,),
) -> None:
    """Check HTTP status code.

    Args:
        status_code: HTTP status code
        content: Optional response content
        expected_codes: Tuple of expected status codes

    Raises:
        ResponseError: If status code is not expected
    """
    if status_code not in expected_codes:
        message = f"Unexpected status code: {status_code}"
        if content:
            message += f" - Response: {content[:200]}"
            if len(content) > 200:
                message += "..."
        raise ResponseError(message, status_code=status_code)

def get_content_type(headers: HeadersType) -> Optional[str]:
    """Get content type from headers.

    Args:
        headers: HTTP headers

    Returns:
        Content type or None if not found
    """
    content_type = headers.get("Content-Type", headers.get("content-type"))
    if content_type:
        # Extract main content type if there are parameters
        return content_type.split(";")[0].strip()
    return None

def is_json_content(headers: HeadersType) -> bool:
    """Check if content type is JSON.

    Args:
        headers: HTTP headers

    Returns:
        True if content type is JSON, False otherwise
    """
    content_type = get_content_type(headers)
    if content_type:
        return content_type.lower() in (
            "application/json",
            "application/problem+json",
            "application/json-patch+json",
        )
    return False

def format_headers(headers: HeadersType) -> HeadersType:
    """Format HTTP headers.

    Args:
        headers: HTTP headers

    Returns:
        Formatted headers
    """
    formatted_headers = {}
    if headers:
        for key, value in headers.items():
            formatted_key = key.strip()
            # Ensure consistent capitalization for common headers
            if formatted_key.lower() == "content-type":
                formatted_key = "Content-Type"
            elif formatted_key.lower() == "authorization":
                formatted_key = "Authorization"
            elif formatted_key.lower() == "user-agent":
                formatted_key = "User-Agent"
            formatted_headers[formatted_key] = value.strip()
    return formatted_headers

def parse_query_params(
    params: Optional[QueryParamsType] = None,
) -> Dict[str, str]:
    """Parse query parameters.

    Args:
        params: Query parameters as dictionary or string

    Returns:
        Parsed parameters
    """
    if not params:
        return {}

    if isinstance(params, str):
        result = {}
        for param in params.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                result[key] = value
            else:
                result[param] = ""
        return result

    # Convert all values to strings
    return {k: str(v) for k, v in params.items()}

# HTTP Client classes
class HTTPResponse:
    """HTTP response class.

    This class represents an HTTP response.
    """

    def __init__(self, status: int, data: bytes, headers: HeadersType):
        """Initialize the response.

        Args:
            status: HTTP status code
            data: Response data
            headers: Response headers
        """
        self._status = status
        self._data = data
        self._headers = headers

    @property
    def status(self) -> int:
        """Get the status code.

        Returns:
            HTTP status code
        """
        return self._status

    @property
    def headers(self) -> HeadersType:
        """Get the headers.

        Returns:
            Response headers
        """
        return self._headers

    def json(self) -> JsonType:
        """Get response data as JSON.

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If response is not valid JSON
        """
        return parse_json(self._data.decode())

    def text(self) -> str:
        """Get response data as text.

        Returns:
            Response text
        """
        return self._data.decode()

class HTTPClient:
    """HTTP client class.

    This class provides a simple HTTP client with async support.
    """

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the client.

        Args:
            base_url: Optional base URL for all requests
        """
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        """Start the client session."""
        self._session = aiohttp.ClientSession()

    async def stop(self) -> None:
        """Stop the client session."""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_url(self, url: str) -> str:
        """Get full URL.

        Args:
            url: URL path or full URL

        Returns:
            Full URL
        """
        if self.base_url and not url.startswith(("http://", "https://")):
            return urljoin(self.base_url, url)
        return url

    async def get(
        self,
        url: str,
        headers: Optional[HeadersType] = None,
    ) -> HTTPResponse:
        """Send GET request.

        Args:
            url: URL to request
            headers: Optional request headers

        Returns:
            HTTP response

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If request times out
            RequestError: If request preparation fails
            ResponseError: If response processing fails
        """
        if not self._session:
            raise ConnectionError("Client session not started")

        try:
            async with self._session.get(
                self._get_url(url),
                headers=format_headers(headers or {}),
            ) as response:
                data = await response.read()
                return HTTPResponse(
                    response.status,
                    data,
                    dict(response.headers),
                )
        except aiohttp.ClientError as e:
            raise ConnectionError(str(e))
        except asyncio.TimeoutError as e:
            raise TimeoutError(str(e))

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersType] = None,
    ) -> HTTPResponse:
        """Send POST request.

        Args:
            url: URL to request
            data: Optional request data
            headers: Optional request headers

        Returns:
            HTTP response

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If request times out
            RequestError: If request preparation fails
            ResponseError: If response processing fails
        """
        if not self._session:
            raise ConnectionError("Client session not started")

        try:
            async with self._session.post(
                self._get_url(url),
                json=data,
                headers=format_headers(headers or {}),
            ) as response:
                data = await response.read()
                return HTTPResponse(
                    response.status,
                    data,
                    dict(response.headers),
                )
        except aiohttp.ClientError as e:
            raise ConnectionError(str(e))
        except asyncio.TimeoutError as e:
            raise TimeoutError(str(e))

    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersType] = None,
    ) -> HTTPResponse:
        """Send PUT request.

        Args:
            url: URL to request
            data: Optional request data
            headers: Optional request headers

        Returns:
            HTTP response

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If request times out
            RequestError: If request preparation fails
            ResponseError: If response processing fails
        """
        if not self._session:
            raise ConnectionError("Client session not started")

        try:
            async with self._session.put(
                self._get_url(url),
                json=data,
                headers=format_headers(headers or {}),
            ) as response:
                data = await response.read()
                return HTTPResponse(
                    response.status,
                    data,
                    dict(response.headers),
                )
        except aiohttp.ClientError as e:
            raise ConnectionError(str(e))
        except asyncio.TimeoutError as e:
            raise TimeoutError(str(e))

    async def delete(
        self,
        url: str,
        headers: Optional[HeadersType] = None,
    ) -> HTTPResponse:
        """Send DELETE request.

        Args:
            url: URL to request
            headers: Optional request headers

        Returns:
            HTTP response

        Raises:
            ConnectionError: If connection fails
            TimeoutError: If request times out
            RequestError: If request preparation fails
            ResponseError: If response processing fails
        """
        if not self._session:
            raise ConnectionError("Client session not started")

        try:
            async with self._session.delete(
                self._get_url(url),
                headers=format_headers(headers or {}),
            ) as response:
                data = await response.read()
                return HTTPResponse(
                    response.status,
                    data,
                    dict(response.headers),
                )
        except aiohttp.ClientError as e:
            raise ConnectionError(str(e))
        except asyncio.TimeoutError as e:
            raise TimeoutError(str(e))
