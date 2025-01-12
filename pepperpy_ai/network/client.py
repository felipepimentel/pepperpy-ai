"""Network client module."""

from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast, Coroutine

import aiohttp
from aiohttp import ClientResponse, ClientSession

from ..exceptions import ProviderError

T = TypeVar("T")


def handle_errors(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
    """Handle network errors.

    Args:
        func: The async function to wrap.

    Returns:
        The wrapped async function.
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientError as e:
            raise ProviderError(f"Network error: {e}", provider="network")
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}", provider="network")
    return wrapper


class NetworkClient:
    """Network client for making HTTP requests."""

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """Initialize the client.

        Args:
            base_url: The base URL for requests.
            headers: Optional headers to include in requests.
        """
        self.base_url = base_url
        self.headers = headers or {}
        self._session: Optional[ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the client session."""
        if not self._session:
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=self.headers
            )

    async def cleanup(self) -> None:
        """Clean up the client session."""
        if self._session:
            await self._session.close()
            self._session = None

    @handle_errors
    async def get(self, path: str, **kwargs: Any) -> ClientResponse:
        """Make a GET request.

        Args:
            path: The request path.
            **kwargs: Additional request arguments.

        Returns:
            The response.

        Raises:
            ProviderError: If the request fails.
        """
        if not self._session:
            await self.initialize()
        assert self._session is not None
        return await self._session.get(path, **kwargs)

    @handle_errors
    async def post(self, path: str, **kwargs: Any) -> ClientResponse:
        """Make a POST request.

        Args:
            path: The request path.
            **kwargs: Additional request arguments.

        Returns:
            The response.

        Raises:
            ProviderError: If the request fails.
        """
        if not self._session:
            await self.initialize()
        assert self._session is not None
        return await self._session.post(path, **kwargs)

    @handle_errors
    async def put(self, path: str, **kwargs: Any) -> ClientResponse:
        """Make a PUT request.

        Args:
            path: The request path.
            **kwargs: Additional request arguments.

        Returns:
            The response.

        Raises:
            ProviderError: If the request fails.
        """
        if not self._session:
            await self.initialize()
        assert self._session is not None
        return await self._session.put(path, **kwargs)

    @handle_errors
    async def delete(self, path: str, **kwargs: Any) -> ClientResponse:
        """Make a DELETE request.

        Args:
            path: The request path.
            **kwargs: Additional request arguments.

        Returns:
            The response.

        Raises:
            ProviderError: If the request fails.
        """
        if not self._session:
            await self.initialize()
        assert self._session is not None
        return await self._session.delete(path, **kwargs)
