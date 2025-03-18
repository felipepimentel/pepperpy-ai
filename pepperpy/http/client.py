"""HTTP client connection pool implementation.

This module provides an implementation of connection pooling for HTTP clients,
which helps optimize HTTP requests by reusing existing connections.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import httpx
from httpx import URL, AsyncClient
from httpx import Response as HTTPXResponse

from pepperpy.core.errors import PepperPyError
from pepperpy.core.logging import get_logger
from pepperpy.infra.connection import ConnectionPool, ConnectionPoolConfig

# Logger for this module
logger = get_logger(__name__)

# Type variable for decorator return type
T = TypeVar("T")

# Default pool name
_default_pool_name = "default"


@dataclass
class HTTPPoolConfig(ConnectionPoolConfig):
    """Configuration for HTTP connection pools."""

    # HTTP-specific settings
    base_url: Optional[str] = None
    timeout: float = 60.0
    follow_redirects: bool = True
    verify_ssl: bool = True
    default_headers: Dict[str, str] = field(default_factory=dict)
    default_cookies: Dict[str, str] = field(default_factory=dict)
    limits: Optional[httpx.Limits] = None
    http2: bool = False
    proxy: Optional[Union[str, Dict[str, str]]] = None


class RequestOptions:
    """Options for HTTP requests."""

    def __init__(
        self,
        timeout: float = 60.0,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        files: Optional[Dict[str, Any]] = None,
        auth: Optional[Any] = None,
    ):
        """Initialize request options.

        Args:
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow redirects
            verify_ssl: Whether to verify SSL certificates
            headers: HTTP headers
            cookies: HTTP cookies
            params: Query parameters
            json: JSON body
            data: Form data
            files: Files to upload
            auth: Authentication
        """
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.params = params
        self.json = json
        self.data = data
        self.files = files
        self.auth = auth


class Response:
    """HTTP response wrapper."""

    def __init__(
        self,
        status_code: int,
        content: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        url: Optional[str] = None,
        elapsed: Optional[float] = None,
    ):
        """Initialize a response.

        Args:
            status_code: HTTP status code
            content: Response content
            headers: Response headers
            cookies: Response cookies
            url: Response URL
            elapsed: Time elapsed for the request
        """
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.url = url
        self.elapsed = elapsed

    @property
    def text(self) -> str:
        """Get the response content as text.

        Returns:
            The response content as text
        """
        return self.content.decode("utf-8")

    def json(self) -> Any:
        """Get the response content as JSON.

        Returns:
            The response content as JSON

        Raises:
            ValueError: If the response content is not valid JSON
        """
        import json

        return json.loads(self.text)

    def raise_for_status(self) -> None:
        """Raise an exception if the response status code indicates an error.

        Raises:
            HTTPError: If the response status code indicates an error
        """
        if self.status_code >= 400:
            raise HTTPError(f"HTTP error {self.status_code}: {self.text}")

    @classmethod
    def from_httpx_response(cls, response: HTTPXResponse) -> "Response":
        """Create a Response from an HTTPX response.

        Args:
            response: HTTPX response

        Returns:
            A Response instance
        """
        return cls(
            status_code=response.status_code,
            content=response.content,
            headers=dict(response.headers),
            cookies=dict(response.cookies),
            url=str(response.url),
            elapsed=response.elapsed.total_seconds(),
        )


class HTTPError(PepperPyError):
    """Error raised when an HTTP request fails."""

    pass


class HTTPXClient:
    """HTTP client wrapper around HTTPX."""

    def __init__(
        self,
        base_url: Optional[Union[str, URL]] = None,
        default_options: Optional[RequestOptions] = None,
    ):
        """Initialize an HTTP client.

        Args:
            base_url: Base URL for requests
            default_options: Default request options
        """
        self.base_url = base_url  # type: ignore
        self.default_options = default_options or RequestOptions()
        self._client: Optional[AsyncClient] = None

    async def _ensure_client(self) -> AsyncClient:
        """Ensure the HTTPX client is initialized.

        Returns:
            The HTTPX client
        """
        if self._client is None:
            # Convert None to empty string for base_url to avoid type error
            base_url_value = self.base_url if self.base_url is not None else ""
            self._client = AsyncClient(
                base_url=base_url_value,
                timeout=self.default_options.timeout,
                follow_redirects=self.default_options.follow_redirects,
                verify=self.default_options.verify_ssl,
                headers=self.default_options.headers,
                cookies=self.default_options.cookies,
            )
        return self._client

    async def close(self) -> None:
        """Close the client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def request(
        self, method: str, url: str, options: Optional[RequestOptions] = None
    ) -> Response:
        """Make an HTTP request.

        Args:
            method: HTTP method
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        options = options or self.default_options
        client = await self._ensure_client()

        try:
            response = await client.request(
                method=method,
                url=url,
                headers=options.headers,
                cookies=options.cookies,
                params=options.params,
                json=options.json,
                data=options.data,
                files=options.files,
                auth=options.auth,
                timeout=options.timeout,
                follow_redirects=options.follow_redirects,
            )
            return Response.from_httpx_response(response)
        except httpx.HTTPError as e:
            raise HTTPError(f"HTTP request failed: {str(e)}") from e

    async def get(self, url: str, options: Optional[RequestOptions] = None) -> Response:
        """Make a GET request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("GET", url, options)

    async def post(
        self, url: str, options: Optional[RequestOptions] = None
    ) -> Response:
        """Make a POST request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("POST", url, options)

    async def put(self, url: str, options: Optional[RequestOptions] = None) -> Response:
        """Make a PUT request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("PUT", url, options)

    async def delete(
        self, url: str, options: Optional[RequestOptions] = None
    ) -> Response:
        """Make a DELETE request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("DELETE", url, options)

    async def head(
        self, url: str, options: Optional[RequestOptions] = None
    ) -> Response:
        """Make a HEAD request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("HEAD", url, options)

    async def options(
        self, url: str, options: Optional[RequestOptions] = None
    ) -> Response:
        """Make an OPTIONS request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("OPTIONS", url, options)

    async def patch(
        self, url: str, options: Optional[RequestOptions] = None
    ) -> Response:
        """Make a PATCH request.

        Args:
            url: URL to request
            options: Request options

        Returns:
            The HTTP response

        Raises:
            HTTPError: If the request fails
        """
        return await self.request("PATCH", url, options)


class HTTPConnectionPool(ConnectionPool):
    """Connection pool for HTTP clients.

    This pool manages HTTPXClient instances, allowing them to be reused
    across multiple requests.
    """

    def __init__(
        self,
        name: str,
        config: Optional[HTTPPoolConfig] = None,
    ):
        """Initialize an HTTP connection pool.

        Args:
            name: Name of the pool
            config: Pool configuration
        """
        config = config or self._get_default_config()
        super().__init__(name, config)

    def _get_default_config(self) -> HTTPPoolConfig:
        """Get the default pool configuration.

        Returns:
            The default pool configuration
        """
        return HTTPPoolConfig(
            max_size=10,
            max_lifetime=300,
            idle_timeout=60,
        )

    async def _create_connection(self) -> HTTPXClient:
        """Create a new HTTP client.

        Returns:
            A new HTTP client

        Raises:
            PepperPyError: If the client cannot be created
        """
        config = self.config
        if not isinstance(config, HTTPPoolConfig):
            raise PepperPyError(
                f"Invalid config type for HTTP pool: {type(config).__name__}"
            )

        try:
            # Create default options
            default_options = RequestOptions(
                timeout=config.timeout,
                follow_redirects=config.follow_redirects,
                verify_ssl=config.verify_ssl,
                headers=config.default_headers,
                cookies=config.default_cookies,
            )

            # Create client
            client = HTTPXClient(
                base_url=config.base_url,
                default_options=default_options,
            )

            logger.debug(f"Created new HTTP client for pool {self.name}")
            return client
        except Exception as e:
            raise PepperPyError(f"Failed to create HTTP client: {str(e)}") from e

    async def _close_connection(self, connection: HTTPXClient) -> None:
        """Close an HTTP client.

        Args:
            connection: The HTTP client to close
        """
        try:
            await connection.close()
            logger.debug(f"Closed HTTP client for pool {self.name}")
        except Exception as e:
            logger.warning(f"Error closing HTTP client: {str(e)}")

    async def _validate_connection(self, connection: HTTPXClient) -> bool:
        """Validate an HTTP client.

        Args:
            connection: The HTTP client to validate

        Returns:
            True if the client is valid, False otherwise
        """
        # For now, we assume the client is valid if it exists
        # In a real implementation, we might want to make a test request
        return connection is not None


# Global registry of HTTP pools
_http_pools: Dict[str, HTTPConnectionPool] = {}


def create_http_pool(
    name: str,
    config: Optional[HTTPPoolConfig] = None,
) -> HTTPConnectionPool:
    """Create an HTTP connection pool.

    Args:
        name: Name of the pool
        config: Pool configuration

    Returns:
        The HTTP connection pool

    Raises:
        PepperPyError: If a pool with the same name already exists
    """
    if name in _http_pools:
        raise PepperPyError(f"HTTP pool already exists: {name}")

    pool = HTTPConnectionPool(name, config)
    _http_pools[name] = pool

    logger.info(f"Created HTTP pool: {name}")
    return pool


def get_http_pool(name: str = _default_pool_name) -> HTTPConnectionPool:
    """Get an HTTP connection pool.

    Args:
        name: Name of the pool

    Returns:
        The HTTP connection pool

    Raises:
        PepperPyError: If the pool does not exist
    """
    if name not in _http_pools:
        raise PepperPyError(f"HTTP pool not found: {name}")

    return _http_pools[name]


async def initialize_default_http_pool() -> None:
    """Initialize the default HTTP pool.

    This function creates the default HTTP pool if it doesn't exist.
    """
    if _default_pool_name not in _http_pools:
        config = HTTPPoolConfig(
            max_size=10,
            max_lifetime=300,
            idle_timeout=60,
            timeout=60.0,
            follow_redirects=True,
            verify_ssl=True,
        )
        create_http_pool(_default_pool_name, config)
        logger.info("Initialized default HTTP pool")


async def get_http_client(pool_name: str = _default_pool_name) -> HTTPXClient:
    """Get an HTTP client from a pool.

    Args:
        pool_name: Name of the pool

    Returns:
        An HTTP client

    Raises:
        PepperPyError: If the pool does not exist or the client cannot be acquired
    """
    pool = get_http_pool(pool_name)
    client = await pool.acquire()
    logger.debug(f"Acquired HTTP client from pool {pool_name}")
    return client


async def release_http_client(
    client: HTTPXClient,
    pool_name: str = _default_pool_name,
) -> None:
    """Release an HTTP client back to a pool.

    Args:
        client: The HTTP client to release
        pool_name: Name of the pool

    Raises:
        PepperPyError: If the pool does not exist or the client cannot be released
    """
    pool = get_http_pool(pool_name)
    await pool.release(client)
    logger.debug(f"Released HTTP client back to pool {pool_name}")


class HTTPClientContext:
    """Context manager for HTTP clients.

    This context manager acquires an HTTP client from a pool and releases
    it back to the pool when the context is exited.
    """

    def __init__(self, pool_name: str = _default_pool_name):
        """Initialize the context manager.

        Args:
            pool_name: Name of the pool
        """
        self.pool_name = pool_name
        self.client: Optional[HTTPXClient] = None

    async def __aenter__(self) -> HTTPXClient:
        """Enter the context.

        Returns:
            An HTTP client

        Raises:
            PepperPyError: If the client cannot be acquired
        """
        self.client = await get_http_client(self.pool_name)
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.client is not None:
            await release_http_client(self.client, self.pool_name)
            self.client = None


def http_client(
    pool_name: str = _default_pool_name,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for functions that need an HTTP client.

    This decorator acquires an HTTP client from a pool and passes it to
    the decorated function as the first argument.

    Args:
        pool_name: Name of the pool

    Returns:
        A decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            async with HTTPClientContext(pool_name) as client:
                return await func(client, *args, **kwargs)

        return wrapper

    return decorator


async def request(
    method: str,
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make an HTTP request.

    Args:
        method: HTTP method
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    async with HTTPClientContext(pool_name) as client:
        return await client.request(method, url, options)


async def get(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a GET request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("GET", url, options, pool_name)


async def post(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a POST request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("POST", url, options, pool_name)


async def put(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a PUT request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("PUT", url, options, pool_name)


async def delete(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a DELETE request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("DELETE", url, options, pool_name)


async def head(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a HEAD request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("HEAD", url, options, pool_name)


async def options(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make an OPTIONS request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("OPTIONS", url, options, pool_name)


async def patch(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a PATCH request.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        The HTTP response

    Raises:
        HTTPError: If the request fails
    """
    return await request("PATCH", url, options, pool_name)


__all__ = [
    # Classes
    "HTTPPoolConfig",
    "RequestOptions",
    "Response",
    "HTTPError",
    "HTTPXClient",
    "HTTPConnectionPool",
    "HTTPClientContext",
    # Functions
    "create_http_pool",
    "get_http_pool",
    "initialize_default_http_pool",
    "get_http_client",
    "release_http_client",
    "http_client",
    # HTTP methods
    "request",
    "get",
    "post",
    "put",
    "delete",
    "head",
    "options",
    "patch",
]
