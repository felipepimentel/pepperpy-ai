"""HTTP utilities for PepperPy.

This module provides HTTP client functionality and utilities for the PepperPy framework,
including a client, error handling, and helper functions.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urljoin

import aiohttp


# Error classes
class HTTPError(Exception):
    """Base class for HTTP errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize HTTP error.

        Args:
            message: Error message
            status_code: Optional HTTP status code
        """
        super().__init__(message)
        self.status_code = status_code


class RequestError(HTTPError):
    """Error during HTTP request preparation."""

    pass


class ResponseError(HTTPError):
    """Error in HTTP response."""

    pass


class ConnectionError(HTTPError):
    """Error connecting to HTTP server."""

    pass


class TimeoutError(HTTPError):
    """HTTP request timeout."""

    pass


# Helper functions
def parse_json(content: str) -> Any:
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
    expected_codes: Tuple[int, ...] = (200,),
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


def get_content_type(headers: Dict[str, str]) -> Optional[str]:
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


def is_json_content(headers: Dict[str, str]) -> bool:
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


def format_headers(headers: Dict[str, str]) -> Dict[str, str]:
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
    params: Optional[Union[Dict[str, Any], str]] = None,
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

    def __init__(self, status: int, data: bytes, headers: Dict[str, str]):
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
    def headers(self) -> Dict[str, str]:
        """Get the headers.

        Returns:
            Response headers
        """
        return self._headers

    def json(self) -> Any:
        """Get the response data as JSON.

        Returns:
            JSON data

        Raises:
            ValueError: If the response is not valid JSON
        """
        return parse_json(self.text())

    def text(self) -> str:
        """Get the response data as text.

        Returns:
            Response text
        """
        return self._data.decode("utf-8")


class HTTPClient:
    """HTTP client.

    This class provides HTTP client functionality.
    """

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the client.

        Args:
            base_url: Optional base URL for requests
        """
        self._base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the client session."""
        self._session = aiohttp.ClientSession()

    async def stop(self) -> None:
        """Stop the client session."""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_url(self, url: str) -> str:
        """Get the full URL.

        Args:
            url: URL path or full URL

        Returns:
            Full URL
        """
        if self._base_url and not url.startswith(("http://", "https://", "file://")):
            return urljoin(self._base_url, url)
        return url

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Send a GET request.

        Args:
            url: URL
            headers: Optional headers

        Returns:
            HTTP response

        Raises:
            RequestError: If the request fails
            ConnectionError: If the connection fails
            TimeoutError: If the request times out
        """
        if not self._session:
            await self.start()
            if not self._session:
                raise RequestError("Failed to create session")

        full_url = self._get_url(url)
        formatted_headers = format_headers(headers or {})

        try:
            async with self._session.get(
                full_url, headers=formatted_headers
            ) as response:
                data = await response.read()
                return HTTPResponse(response.status, data, dict(response.headers))
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {full_url} timed out")
        except Exception as e:
            raise RequestError(f"Request error: {e}")

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> HTTPResponse:
        """Send a POST request.

        Args:
            url: URL
            data: Optional JSON data
            headers: Optional headers

        Returns:
            HTTP response

        Raises:
            RequestError: If the request fails
            ConnectionError: If the connection fails
            TimeoutError: If the request times out
        """
        if not self._session:
            await self.start()
            if not self._session:
                raise RequestError("Failed to create session")

        full_url = self._get_url(url)
        formatted_headers = format_headers(headers or {})

        # Set content type if not specified
        if data and "Content-Type" not in formatted_headers:
            formatted_headers["Content-Type"] = "application/json"

        try:
            async with self._session.post(
                full_url, json=data, headers=formatted_headers
            ) as response:
                response_data = await response.read()
                return HTTPResponse(
                    response.status, response_data, dict(response.headers)
                )
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request to {full_url} timed out")
        except Exception as e:
            raise RequestError(f"Request error: {e}")
