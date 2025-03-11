"""Core functionality for HTTP client.

This module provides the core functionality for HTTP client,
including request handling, response parsing, and session management.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import httpx

from pepperpy.http.errors import (
    ClientError,
    ConnectionError,
    RequestError,
    TimeoutError,
)
from pepperpy.http.utils import check_status_code, parse_json
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


@dataclass
class RequestOptions:
    """Options for HTTP requests.

    Attributes:
        timeout: The timeout for the request in seconds
        retries: The number of times to retry the request
        retry_delay: The delay between retries in seconds
        follow_redirects: Whether to follow redirects
        verify_ssl: Whether to verify SSL certificates
        headers: Additional headers to include in the request
        cookies: Cookies to include in the request
        auth: Authentication credentials
        params: Query parameters to include in the request
        json: JSON data to include in the request body
        data: Form data to include in the request body
        files: Files to include in the request
    """

    timeout: float = 60.0
    retries: int = 3
    retry_delay: float = 1.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Tuple[str, str]] = None
    params: Dict[str, Any] = field(default_factory=dict)
    json: Optional[Any] = None
    data: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """HTTP response.

    Attributes:
        status_code: The HTTP status code
        headers: Dict[str, str]
        cookies: Dict[str, str]
        content: bytes
        text: str
        url: str
        elapsed: float
        _json: Optional[Any] = None
    """

    status_code: int
    headers: Dict[str, str]
    cookies: Dict[str, str]
    content: bytes
    text: str
    url: str
    elapsed: float
    _json: Optional[Any] = None

    @property
    def json(self) -> Any:
        """Get the response content as JSON.

        Returns:
            The response content as JSON

        Raises:
            ResponseError: If the response content is not valid JSON
        """
        if self._json is None:
            self._json = parse_json(self.text, self.status_code)
        return self._json

    def raise_for_status(self) -> None:
        """Raise an exception if the response status code indicates an error.

        Raises:
            ResponseError: If the response status code indicates an error
        """
        check_status_code(self.status_code)


class HTTPClient(ABC):
    """Base class for HTTP clients.

    HTTP clients are responsible for making HTTP requests and handling responses.
    """

    @abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make an HTTP request.

        Args:
            method: The HTTP method to use
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def get(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a GET request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def post(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a POST request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def put(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a PUT request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def delete(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a DELETE request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def patch(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a PATCH request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def head(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a HEAD request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def options(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make an OPTIONS request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the client and release resources."""
        pass


class HTTPXClient(HTTPClient):
    """HTTP client implementation using HTTPX.

    This client uses the HTTPX library to make HTTP requests.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_options: Optional[RequestOptions] = None,
    ):
        """Initialize an HTTPX client.

        Args:
            base_url: The base URL for all requests
            default_options: Default options for all requests
        """
        self.base_url = base_url
        self.default_options = default_options or RequestOptions()

        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=self.default_options.timeout,
            follow_redirects=self.default_options.follow_redirects,
            verify=self.default_options.verify_ssl,
        )

    async def request(
        self,
        method: str,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make an HTTP request.

        Args:
            method: The HTTP method to use
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        # Merge options with default options
        merged_options = self._merge_options(options)

        # Prepare request parameters
        request_kwargs = {
            "method": method,
            "url": url,
            "headers": merged_options.headers,
            "cookies": merged_options.cookies,
            "params": merged_options.params,
            "json": merged_options.json,
            "data": merged_options.data,
            "files": merged_options.files,
            "auth": merged_options.auth,
            "timeout": merged_options.timeout,
            "follow_redirects": merged_options.follow_redirects,
        }

        # Make the request with retries
        retries = merged_options.retries
        retry_delay = merged_options.retry_delay

        for attempt in range(retries):
            try:
                # Make the request
                start_time = asyncio.get_event_loop().time()
                httpx_response = await self.client.request(**request_kwargs)
                elapsed = asyncio.get_event_loop().time() - start_time

                # Convert the response
                response = Response(
                    status_code=httpx_response.status_code,
                    headers=dict(httpx_response.headers),
                    cookies=dict(httpx_response.cookies),
                    content=httpx_response.content,
                    text=httpx_response.text,
                    url=str(httpx_response.url),
                    elapsed=elapsed,
                )

                return response
            except httpx.TimeoutException as e:
                if attempt == retries - 1:
                    raise TimeoutError(
                        f"Request timed out after {merged_options.timeout} seconds",
                    ) from e

                # Wait before retrying
                await asyncio.sleep(retry_delay)
            except httpx.ConnectError as e:
                if attempt == retries - 1:
                    raise ConnectionError(
                        f"Failed to connect to {url}",
                    ) from e

                # Wait before retrying
                await asyncio.sleep(retry_delay)
            except httpx.RequestError as e:
                if attempt == retries - 1:
                    raise RequestError(
                        f"Error making request to {url}: {e}",
                    ) from e

                # Wait before retrying
                await asyncio.sleep(retry_delay)
            except Exception as e:
                if attempt == retries - 1:
                    raise ClientError(
                        f"Unexpected error making request to {url}: {e}",
                    ) from e

                # Wait before retrying
                await asyncio.sleep(retry_delay)

        # This should never be reached due to the exception handling above,
        # but we need to satisfy the type checker
        raise ClientError(f"Failed to make request to {url} after {retries} attempts")

    async def get(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a GET request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("GET", url, options)

    async def post(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a POST request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("POST", url, options)

    async def put(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a PUT request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("PUT", url, options)

    async def delete(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a DELETE request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("DELETE", url, options)

    async def patch(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a PATCH request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("PATCH", url, options)

    async def head(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make a HEAD request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("HEAD", url, options)

    async def options(
        self,
        url: str,
        options: Optional[RequestOptions] = None,
    ) -> Response:
        """Make an OPTIONS request.

        Args:
            url: The URL to request
            options: Options for the request

        Returns:
            The HTTP response

        Raises:
            ClientError: If there is an error making the request
        """
        return await self.request("OPTIONS", url, options)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self.client.aclose()

    def _merge_options(
        self, options: Optional[RequestOptions] = None
    ) -> RequestOptions:
        """Merge options with default options.

        Args:
            options: Options to merge with default options

        Returns:
            The merged options
        """
        if options is None:
            return self.default_options

        # Create a new options object with default values
        merged = RequestOptions(
            timeout=options.timeout or self.default_options.timeout,
            retries=options.retries or self.default_options.retries,
            retry_delay=options.retry_delay or self.default_options.retry_delay,
            follow_redirects=options.follow_redirects
            if options.follow_redirects is not None
            else self.default_options.follow_redirects,
            verify_ssl=options.verify_ssl
            if options.verify_ssl is not None
            else self.default_options.verify_ssl,
            auth=options.auth or self.default_options.auth,
        )

        # Merge headers
        merged.headers = {**self.default_options.headers, **options.headers}

        # Merge cookies
        merged.cookies = {**self.default_options.cookies, **options.cookies}

        # Merge params
        merged.params = {**self.default_options.params, **options.params}

        # Set other fields
        merged.json = options.json
        merged.data = options.data
        merged.files = options.files

        return merged


# Global HTTP client instance
_http_client = HTTPXClient(base_url="https://api.example.com")


def get_http_client() -> HTTPClient:
    """Get the default HTTP client.

    Returns:
        The default HTTP client
    """
    return _http_client


def set_http_client(client: HTTPClient) -> None:
    """Set the default HTTP client.

    Args:
        client: The HTTP client to set as the default
    """
    global _http_client
    _http_client = client


async def request(
    method: str,
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make an HTTP request.

    Args:
        method: The HTTP method to use
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().request(method, url, options)


async def get(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make a GET request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().get(url, options)


async def post(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make a POST request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().post(url, options)


async def put(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make a PUT request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().put(url, options)


async def delete(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make a DELETE request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().delete(url, options)


async def patch(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make a PATCH request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().patch(url, options)


async def head(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make a HEAD request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().head(url, options)


async def options(
    url: str,
    options: Optional[RequestOptions] = None,
) -> Response:
    """Make an OPTIONS request.

    Args:
        url: The URL to request
        options: Options for the request

    Returns:
        The HTTP response

    Raises:
        ClientError: If there is an error making the request
    """
    return await get_http_client().options(url, options)
