"""Network client module."""

import logging
from typing import Any, cast

import aiohttp

from ..types import JsonDict

logger = logging.getLogger(__name__)


class NetworkClient:
    """Network client."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        """Initialize network client.

        Args:
            base_url: Base URL.
            api_key: API key.
        """
        self._base_url = base_url
        self._api_key = api_key
        self._session: aiohttp.ClientSession | None = None

    async def initialize(self) -> None:
        """Initialize client."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                base_url=self._base_url,
                headers=(
                    {"Authorization": f"Bearer {self._api_key}"}
                    if self._api_key
                    else None
                ),
            )

    async def close(self) -> None:
        """Close client."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def get(self, path: str, **kwargs: Any) -> JsonDict:
        """Get request.

        Args:
            path: Path.
            **kwargs: Additional arguments.

        Returns:
            Response data.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if self._session is None:
            raise RuntimeError("Client not initialized")
        async with self._session.get(path, **kwargs) as response:
            response.raise_for_status()
            return cast(JsonDict, await response.json())

    async def post(self, path: str, **kwargs: Any) -> JsonDict:
        """Post request.

        Args:
            path: Path.
            **kwargs: Additional arguments.

        Returns:
            Response data.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if self._session is None:
            raise RuntimeError("Client not initialized")
        async with self._session.post(path, **kwargs) as response:
            response.raise_for_status()
            return cast(JsonDict, await response.json())

    async def put(self, path: str, **kwargs: Any) -> JsonDict:
        """Put request.

        Args:
            path: Path.
            **kwargs: Additional arguments.

        Returns:
            Response data.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if self._session is None:
            raise RuntimeError("Client not initialized")
        async with self._session.put(path, **kwargs) as response:
            response.raise_for_status()
            return cast(JsonDict, await response.json())

    async def delete(self, path: str, **kwargs: Any) -> JsonDict:
        """Delete request.

        Args:
            path: Path.
            **kwargs: Additional arguments.

        Returns:
            Response data.

        Raises:
            RuntimeError: If client is not initialized.
        """
        if self._session is None:
            raise RuntimeError("Client not initialized")
        async with self._session.delete(path, **kwargs) as response:
            response.raise_for_status()
            return cast(JsonDict, await response.json())
