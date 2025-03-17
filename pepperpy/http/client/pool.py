"""HTTP client connection pool implementation.

This module provides an implementation of connection pooling for HTTP clients,
which helps optimize HTTP requests by reusing existing connections.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Union

import httpx
from httpx import URL

from pepperpy.core.connection_pool import (
    get_pool,
    register_pool,
)
from pepperpy.core.errors import PepperPyError
from pepperpy.infra.connection import (
    ConnectionPool,
    ConnectionPoolConfig,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)


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


# Forward reference for type hints
class HTTPXClient:
    """HTTP client implementation using HTTPX."""

    def __init__(
        self,
        base_url: Optional[Union[str, URL]] = None,
        default_options: Optional["RequestOptions"] = None,
    ):
        """Initialize the client."""
        self.base_url = base_url
        self.default_options = default_options
        self.client = None

    async def request(self, method: str, url: str, options=None):
        """Make an HTTP request."""
        pass

    async def head(self, url: str, options=None):
        """Make a HEAD request."""
        pass


class RequestOptions:
    """Options for HTTP requests."""

    def __init__(
        self,
        timeout: float = 60.0,
        follow_redirects: bool = True,
        verify_ssl: bool = True,
        headers: Dict[str, str] = None,
        cookies: Dict[str, str] = None,
    ):
        """Initialize request options."""
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl
        self.headers = headers or {}
        self.cookies = cookies or {}


class Response:
    """HTTP response."""

    def __init__(self, status_code: int, **kwargs):
        """Initialize response."""
        self.status_code = status_code


class HTTPConnectionPool(ConnectionPool):
    """Connection pool for HTTP clients.

    This pool manages HTTPXClient instances for making HTTP requests.
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
        super().__init__(name, config)

    def _get_default_config(self) -> HTTPPoolConfig:
        """Get the default configuration for the pool.

        Returns:
            Default pool configuration
        """
        return HTTPPoolConfig()

    async def _create_connection(self) -> HTTPXClient:
        """Create a new HTTP client.

        Returns:
            New HTTP client

        Raises:
            PepperPyError: If client creation fails
        """
        try:
            # Get configuration values
            config = self.config
            base_url: Optional[str] = getattr(config, "base_url", None)
            timeout = getattr(config, "timeout", 60.0)
            follow_redirects = getattr(config, "follow_redirects", True)
            verify_ssl = getattr(config, "verify_ssl", True)
            default_headers = getattr(config, "default_headers", {}).copy()
            default_cookies = getattr(config, "default_cookies", {}).copy()
            limits = getattr(config, "limits", None)
            http2 = getattr(config, "http2", False)
            proxy = getattr(config, "proxy", None)

            # Create default request options
            default_options = RequestOptions(
                timeout=timeout,
                follow_redirects=follow_redirects,
                verify_ssl=verify_ssl,
                headers=default_headers,
                cookies=default_cookies,
            )

            # Create limits if not provided
            if limits is None:
                limits = httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=5.0,
                )

            # Create client
            client = HTTPXClient(
                base_url=base_url,
                default_options=default_options,
            )

            # Set up the underlying HTTPX client with additional options
            client.client = httpx.AsyncClient(
                base_url=URL(base_url) if base_url is not None else None,
                timeout=timeout,
                follow_redirects=follow_redirects,
                verify=verify_ssl,
                headers=default_headers,
                cookies=default_cookies,
                limits=limits,
                http2=http2,
                proxy=proxy,
            )

            return client
        except Exception as e:
            raise PepperPyError(f"Failed to create HTTP client: {e}") from e

    async def _close_connection(self, connection: HTTPXClient) -> None:
        """Close an HTTP client.

        Args:
            connection: HTTP client to close

        Raises:
            PepperPyError: If client closure fails
        """
        try:
            await connection.client.aclose()
        except Exception as e:
            raise PepperPyError(f"Failed to close HTTP client: {e}") from e

    async def _validate_connection(self, connection: HTTPXClient) -> bool:
        """Validate an HTTP client.

        This method checks if the client is still usable by making a simple request.

        Args:
            connection: HTTP client to validate

        Returns:
            True if the client is valid, False otherwise
        """
        try:
            # Try to make a simple HEAD request to the base URL or a known endpoint
            base_url: Optional[str] = getattr(self.config, "base_url", None)
            url = base_url or "https://httpbin.org/status/200"
            options = RequestOptions(timeout=5.0)  # Short timeout for validation

            response = await connection.head(url, options)
            return response.status_code < 500  # Consider any non-server error as valid
        except Exception:
            return False


# Default HTTP connection pool
_default_pool_name = "default_http_pool"


def create_http_pool(
    name: str,
    config: Optional[HTTPPoolConfig] = None,
) -> HTTPConnectionPool:
    """Create an HTTP connection pool.

    Args:
        name: Name of the pool
        config: Pool configuration

    Returns:
        HTTP connection pool

    Raises:
        PepperPyError: If a pool with the same name is already registered
    """
    pool = HTTPConnectionPool(name, config)
    register_pool(pool)
    return pool


def get_http_pool(name: str = _default_pool_name) -> HTTPConnectionPool:
    """Get an HTTP connection pool by name.

    Args:
        name: Name of the pool

    Returns:
        HTTP connection pool

    Raises:
        PepperPyError: If the pool is not registered
    """
    pool = get_pool(name)
    if not isinstance(pool, HTTPConnectionPool):
        raise PepperPyError(f"Pool '{name}' is not an HTTP connection pool")
    return pool


async def initialize_default_http_pool() -> None:
    """Initialize the default HTTP connection pool.

    This function creates and initializes the default HTTP connection pool
    if it doesn't exist.

    Raises:
        PepperPyError: If initialization fails
    """
    try:
        get_http_pool()
    except PepperPyError:
        # Create default pool
        pool = create_http_pool(_default_pool_name)
        await pool.initialize()


async def get_http_client(pool_name: str = _default_pool_name) -> HTTPXClient:
    """Get an HTTP client from a pool.

    Args:
        pool_name: Name of the pool

    Returns:
        HTTP client from the pool

    Raises:
        PepperPyError: If the pool is not registered or a client cannot be acquired
    """
    pool = get_http_pool(pool_name)
    return await pool.acquire()


async def release_http_client(
    client: HTTPXClient,
    pool_name: str = _default_pool_name,
) -> None:
    """Release an HTTP client back to a pool.

    Args:
        client: HTTP client to release
        pool_name: Name of the pool

    Raises:
        PepperPyError: If the pool is not registered or the client is not in use
    """
    pool = get_http_pool(pool_name)
    await pool.release(client)


class HTTPClientContext:
    """Context manager for HTTP clients.

    This context manager acquires an HTTP client from a pool and releases it
    when the context is exited.
    """

    def __init__(self, pool_name: str = _default_pool_name):
        """Initialize an HTTP client context.

        Args:
            pool_name: Name of the pool
        """
        self.pool_name = pool_name
        self.client: Optional[HTTPXClient] = None

    async def __aenter__(self) -> HTTPXClient:
        """Enter the context.

        Returns:
            HTTP client from the pool

        Raises:
            PepperPyError: If a client cannot be acquired
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


def http_client(pool_name: str = _default_pool_name):
    """Decorator for functions that use HTTP clients.

    This decorator wraps a function to acquire an HTTP client from a pool
    and release it when the function returns.

    Args:
        pool_name: Name of the pool

    Returns:
        Decorated function
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            async with HTTPClientContext(pool_name) as client:
                return await func(client, *args, **kwargs)

        return wrapper

    return decorator


# Convenience functions for making HTTP requests with pooled clients
async def request(
    method: str,
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make an HTTP request using a pooled client.

    Args:
        method: HTTP method
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    async with HTTPClientContext(pool_name) as client:
        return await client.request(method, url, options)


async def get(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a GET request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("GET", url, options, pool_name)


async def post(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a POST request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("POST", url, options, pool_name)


async def put(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a PUT request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("PUT", url, options, pool_name)


async def delete(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a DELETE request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("DELETE", url, options, pool_name)


async def head(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a HEAD request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("HEAD", url, options, pool_name)


async def options(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make an OPTIONS request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("OPTIONS", url, options, pool_name)


async def patch(
    url: str,
    options: Optional[RequestOptions] = None,
    pool_name: str = _default_pool_name,
) -> Response:
    """Make a PATCH request using a pooled client.

    Args:
        url: URL to request
        options: Request options
        pool_name: Name of the pool

    Returns:
        HTTP response

    Raises:
        PepperPyError: If the request fails
    """
    return await request("PATCH", url, options, pool_name)
