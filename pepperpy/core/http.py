"""HTTP client for PepperPy.

This module provides a simple HTTP client for making requests to external services.
It supports both synchronous and asynchronous operations, with automatic retries
and error handling.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode

import aiohttp
import requests

from pepperpy.core.base import HeadersType, JsonType, QueryParamsType

logger = logging.getLogger(__name__)


@dataclass
class HTTPResponse:
    """Response from an HTTP request."""

    status: int
    headers: Dict[str, str]
    content: Union[str, bytes]
    json: Optional[JsonType] = None

    def __post_init__(self) -> None:
        """Parse JSON content if possible."""
        if isinstance(self.content, str) and self.content:
            try:
                self.json = json.loads(self.content)
            except json.JSONDecodeError:
                pass


class HTTPClient:
    """HTTP client for making requests."""

    def __init__(
        self,
        base_url: str = "",
        headers: Optional[HeadersType] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize HTTP client.

        Args:
            base_url: Base URL for all requests
            headers: Default headers to include
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.verify_ssl = verify_ssl
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "HTTPClient":
        """Enter async context."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize HTTP client."""
        if not self._session:
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )

    async def cleanup(self) -> None:
        """Clean up HTTP client resources."""
        if self._session:
            await self._session.close()
            self._session = None

    def _build_url(self, path: str, params: Optional[QueryParamsType] = None) -> str:
        """Build full URL from path and parameters.

        Args:
            path: URL path
            params: Query parameters

        Returns:
            Full URL with query parameters
        """
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path

        if isinstance(params, str):
            return f"{url}?{params}"
        elif isinstance(params, dict):
            query = urlencode(params)
            return f"{url}?{query}" if query else url
        else:
            return url

    def _merge_headers(self, headers: Optional[HeadersType] = None) -> HeadersType:
        """Merge default headers with request-specific headers.

        Args:
            headers: Request-specific headers

        Returns:
            Merged headers dictionary
        """
        merged = self.headers.copy()
        if headers:
            merged.update(headers)
        return merged

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        json_data: Optional[JsonType] = None,
        data: Optional[Union[str, bytes]] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            params: Query parameters
            headers: Request headers
            json_data: JSON data to send
            data: Raw data to send
            timeout: Request timeout in seconds

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails
        """
        if not self._session:
            await self.initialize()

        url = self._build_url(path, params)
        headers = self._merge_headers(headers)
        timeout = timeout or self.timeout

        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=json_data,
                data=data,
                timeout=timeout,
                ssl=self.verify_ssl,
            ) as response:
                content = await response.read()
                return HTTPResponse(
                    status=response.status,
                    headers=dict(response.headers),
                    content=content,
                )

        except asyncio.TimeoutError as e:
            logger.error(f"Request timed out: {url}")
            raise TimeoutError(f"Request timed out: {url}") from e

        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {url} - {str(e)}")
            raise RequestError(f"Request failed: {str(e)}") from e

    async def get(
        self,
        path: str,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a GET request.

        Args:
            path: URL path
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return await self.request(
            "GET",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    async def post(
        self,
        path: str,
        json_data: Optional[JsonType] = None,
        data: Optional[Union[str, bytes]] = None,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a POST request.

        Args:
            path: URL path
            json_data: JSON data to send
            data: Raw data to send
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return await self.request(
            "POST",
            path,
            json_data=json_data,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    async def put(
        self,
        path: str,
        json_data: Optional[JsonType] = None,
        data: Optional[Union[str, bytes]] = None,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a PUT request.

        Args:
            path: URL path
            json_data: JSON data to send
            data: Raw data to send
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return await self.request(
            "PUT",
            path,
            json_data=json_data,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    async def delete(
        self,
        path: str,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a DELETE request.

        Args:
            path: URL path
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return await self.request(
            "DELETE",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def sync_request(
        self,
        method: str,
        path: str,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        json_data: Optional[JsonType] = None,
        data: Optional[Union[str, bytes]] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a synchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            params: Query parameters
            headers: Request headers
            json_data: JSON data to send
            data: Raw data to send
            timeout: Request timeout in seconds

        Returns:
            HTTP response

        Raises:
            HTTPError: If request fails
        """
        url = self._build_url(path, params)
        headers = self._merge_headers(headers)
        timeout = timeout or self.timeout

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=json_data,
                data=data,
                timeout=timeout,
                verify=self.verify_ssl,
            )
            return HTTPResponse(
                status=response.status_code,
                headers=dict(response.headers),
                content=response.content,
            )

        except requests.Timeout as e:
            logger.error(f"Request timed out: {url}")
            raise TimeoutError(f"Request timed out: {url}") from e

        except requests.RequestException as e:
            logger.error(f"Request failed: {url} - {str(e)}")
            raise RequestError(f"Request failed: {str(e)}") from e

    def sync_get(
        self,
        path: str,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a synchronous GET request.

        Args:
            path: URL path
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return self.sync_request(
            "GET",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def sync_post(
        self,
        path: str,
        json_data: Optional[JsonType] = None,
        data: Optional[Union[str, bytes]] = None,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a synchronous POST request.

        Args:
            path: URL path
            json_data: JSON data to send
            data: Raw data to send
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return self.sync_request(
            "POST",
            path,
            json_data=json_data,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def sync_put(
        self,
        path: str,
        json_data: Optional[JsonType] = None,
        data: Optional[Union[str, bytes]] = None,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a synchronous PUT request.

        Args:
            path: URL path
            json_data: JSON data to send
            data: Raw data to send
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return self.sync_request(
            "PUT",
            path,
            json_data=json_data,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
        )

    def sync_delete(
        self,
        path: str,
        params: Optional[QueryParamsType] = None,
        headers: Optional[HeadersType] = None,
        timeout: Optional[float] = None,
    ) -> HTTPResponse:
        """Make a synchronous DELETE request.

        Args:
            path: URL path
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds

        Returns:
            HTTP response
        """
        return self.sync_request(
            "DELETE",
            path,
            params=params,
            headers=headers,
            timeout=timeout,
        )
