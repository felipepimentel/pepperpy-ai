"""Provider implementations for PepperPy.

This module provides concrete provider implementations for the PepperPy framework.
These providers implement common patterns for local and remote services.

Example:
    >>> from pepperpy.core.providers import RestProvider
    >>> class MyProvider(RestProvider):
    ...     async def fetch_data(self):
    ...         return await self.get("/data")
"""

from typing import Any, Dict, Optional

from pepperpy.core.base import (
    ConfigType,
    HeadersType,
    JsonType,
    BaseProvider,
    RemoteProvider,
    LocalProvider,
    RestProvider,
)
from pepperpy.core.http import HTTPClient

class FileProvider(LocalProvider):
    """Provider for file system operations."""

    def __init__(
        self,
        name: str = "file",
        base_path: Optional[str] = None,
        config: Optional[ConfigType] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the file provider.

        Args:
            name: Provider name
            base_path: Optional base path for file operations
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name, config, **kwargs)
        self.provider_type = "file"
        self.base_path = base_path

class HTTPProvider(RestProvider):
    """Provider for HTTP operations."""

    def __init__(
        self,
        name: str,
        base_url: str,
        config: Optional[ConfigType] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the HTTP provider.

        Args:
            name: Provider name
            base_url: Base URL for API calls
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name, base_url, config, **kwargs)
        self.provider_type = "http"
        self._client: Optional[HTTPClient] = None

    async def _initialize(self) -> None:
        """Initialize the HTTP client."""
        self._client = HTTPClient(self.base_url)
        await self._client.start()

    async def _cleanup(self) -> None:
        """Clean up the HTTP client."""
        if self._client:
            await self._client.stop()
            self._client = None

    async def get(
        self,
        path: str,
        headers: Optional[HeadersType] = None,
        **kwargs: Any,
    ) -> JsonType:
        """Send GET request.

        Args:
            path: API endpoint path
            headers: Optional request headers
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        if not self._client:
            raise RuntimeError("Provider not initialized")

        response = await self._client.get(path, headers=headers)
        return response.json()

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersType] = None,
        **kwargs: Any,
    ) -> JsonType:
        """Send POST request.

        Args:
            path: API endpoint path
            data: Optional request data
            headers: Optional request headers
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        if not self._client:
            raise RuntimeError("Provider not initialized")

        response = await self._client.post(path, data=data, headers=headers)
        return response.json()

    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersType] = None,
        **kwargs: Any,
    ) -> JsonType:
        """Send PUT request.

        Args:
            path: API endpoint path
            data: Optional request data
            headers: Optional request headers
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        if not self._client:
            raise RuntimeError("Provider not initialized")

        response = await self._client.put(path, data=data, headers=headers)
        return response.json()

    async def delete(
        self,
        path: str,
        headers: Optional[HeadersType] = None,
        **kwargs: Any,
    ) -> JsonType:
        """Send DELETE request.

        Args:
            path: API endpoint path
            headers: Optional request headers
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        if not self._client:
            raise RuntimeError("Provider not initialized")

        response = await self._client.delete(path, headers=headers)
        return response.json()
