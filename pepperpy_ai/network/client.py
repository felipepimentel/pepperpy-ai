"""HTTP client module."""

from typing import TypedDict

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from multidict import MultiDict


class RequestData(TypedDict, total=False):
    """Request data parameters."""

    str_value: str | None
    int_value: int | None
    float_value: float | None
    bool_value: bool | None
    list_value: list[str | int | float | bool | None] | None
    dict_value: dict[str, str | int | float | bool | None] | None


class HTTPClient:
    """HTTP client implementation."""

    def __init__(self) -> None:
        """Initialize client."""
        self._session: ClientSession | None = None
        self._initialized = False

    @property
    def session(self) -> ClientSession:
        """Get client session.

        Returns:
            ClientSession: Active client session.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if not self._initialized or not self._session:
            raise RuntimeError("Client not initialized")
        return self._session

    async def initialize(self) -> None:
        """Initialize client."""
        if not self._initialized:
            self._session = aiohttp.ClientSession()
            self._initialized = True

    async def cleanup(self) -> None:
        """Clean up client resources."""
        if self._initialized and self._session:
            await self._session.close()
            self._session = None
            self._initialized = False

    async def get(
        self,
        url: str,
        params: MultiDict | dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        timeout: ClientTimeout | None = None,
        verify_ssl: bool = True,
    ) -> str:
        """Send GET request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            proxy: Proxy URL.
            timeout: Request timeout.
            verify_ssl: Whether to verify SSL certificates.

        Returns:
            str: Response text.
        """
        async with self.session.get(
            url,
            params=params,
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            ssl=verify_ssl,
        ) as response:
            return await response.text()

    async def post(
        self,
        url: str,
        params: MultiDict | dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        timeout: ClientTimeout | None = None,
        verify_ssl: bool = True,
        json: RequestData | None = None,
    ) -> str:
        """Send POST request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            proxy: Proxy URL.
            timeout: Request timeout.
            verify_ssl: Whether to verify SSL certificates.
            json: JSON data to send.

        Returns:
            str: Response text.
        """
        async with self.session.post(
            url,
            params=params,
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            ssl=verify_ssl,
            json=json,
        ) as response:
            return await response.text()

    async def put(
        self,
        url: str,
        params: MultiDict | dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        timeout: ClientTimeout | None = None,
        verify_ssl: bool = True,
        json: RequestData | None = None,
    ) -> str:
        """Send PUT request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            proxy: Proxy URL.
            timeout: Request timeout.
            verify_ssl: Whether to verify SSL certificates.
            json: JSON data to send.

        Returns:
            str: Response text.
        """
        async with self.session.put(
            url,
            params=params,
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            ssl=verify_ssl,
            json=json,
        ) as response:
            return await response.text()

    async def delete(
        self,
        url: str,
        params: MultiDict | dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        proxy: str | None = None,
        timeout: ClientTimeout | None = None,
        verify_ssl: bool = True,
    ) -> str:
        """Send DELETE request.

        Args:
            url: Request URL.
            params: Query parameters.
            headers: Request headers.
            proxy: Proxy URL.
            timeout: Request timeout.
            verify_ssl: Whether to verify SSL certificates.

        Returns:
            str: Response text.
        """
        async with self.session.delete(
            url,
            params=params,
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            ssl=verify_ssl,
        ) as response:
            return await response.text()
