"""Provider implementations for PepperPy.

This module provides concrete provider implementations for the PepperPy framework.
These providers implement common patterns for local and remote services.

Example:
    >>> from pepperpy.core.providers import RestProvider
    >>> class MyProvider(RestProvider):
    ...     async def fetch_data(self):
    ...         return await self.get("/data")
"""

from typing import Any, Dict, Optional, Protocol

from pepperpy.core.http import HTTPClient
from pepperpy.core.types import ConfigType, HeadersType, JsonType


class BaseProvider(Protocol):
    """Base protocol for all providers.

    All providers in PepperPy must implement this protocol to ensure consistent
    behavior across different implementations.
    """

    name: str

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider to set up any
        necessary resources or connections.
        """
        ...

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        ...


class RemoteProvider(BaseProvider):
    """Base class for remote providers.

    This class extends BaseProvider with functionality specific to
    remote services, such as base URL management and API versioning.

    Args:
        name: Provider name
        base_url: Base URL for API calls
        config: Optional configuration dictionary
        **kwargs: Additional provider-specific configuration
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        config: Optional[ConfigType] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the remote provider.

        Args:
            name: Provider name
            base_url: Base URL for API calls
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self.provider_type = "remote"
        self.base_url = base_url.rstrip("/")
        self._config = config or {}
        self._config.update(kwargs)

    def get_endpoint(self, path: str) -> str:
        """Get full endpoint URL.

        Args:
            path: Endpoint path

        Returns:
            Full endpoint URL
        """
        return f"{self.base_url}/{path.lstrip('/')}"


class LocalProvider(BaseProvider):
    """Base class for local providers."""

    def __init__(
        self,
        name: str = "local",
        config: Optional[ConfigType] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the local provider.

        Args:
            name: Provider name
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self.provider_type = "local"
        self._config = config or {}
        self._config.update(kwargs)


class RestProvider(RemoteProvider):
    """Base class for REST API providers."""

    async def get(self, path: str, **kwargs: Any) -> Any:
        """Send GET request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError

    async def post(self, path: str, **kwargs: Any) -> Any:
        """Send POST request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError

    async def put(self, path: str, **kwargs: Any) -> Any:
        """Send PUT request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError

    async def delete(self, path: str, **kwargs: Any) -> Any:
        """Send DELETE request.

        Args:
            path: API endpoint path
            **kwargs: Additional request parameters

        Returns:
            Response data
        """
        raise NotImplementedError


class FileProvider(LocalProvider):
    """Provider for file system operations."""

    def __init__(
        self,
        base_path: Optional[str] = None,
        config: Optional[ConfigType] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the file provider.

        Args:
            base_path: Optional base path for file operations
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name="file", config=config, **kwargs)
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
