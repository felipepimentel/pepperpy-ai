"""Provider base classes for PepperPy.

This module defines the base provider interfaces used across the framework.
These providers implement common patterns for local and remote services.

Example:
    >>> from pepperpy.core.providers import RestProvider
    >>> class MyProvider(RestProvider):
    ...     async def fetch_data(self):
    ...         return await self.get("/data")
"""

import abc
from typing import Any, Dict, Optional

from pepperpy.core.config import Config


class BaseProvider(abc.ABC):
    """Base class for all providers."""

    name: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the provider.

        Args:
            config: Optional configuration dictionary
        """
        self.config = Config(config or {})
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        """
        if not self.initialized:
            await self._initialize()
            self.initialized = True

    async def cleanup(self) -> None:
        """Clean up provider resources.

        This method should be called when the provider is no longer needed.
        """
        if self.initialized:
            await self._cleanup()
            self.initialized = False

    async def _initialize(self) -> None:
        """Provider-specific initialization."""
        pass

    async def _cleanup(self) -> None:
        """Provider-specific cleanup."""
        pass


class LocalProvider(BaseProvider):
    """Base class for local providers."""

    name = "local"


class RemoteProvider(BaseProvider):
    """Base class for remote providers."""

    name = "remote"

    def __init__(
        self,
        base_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the remote provider.

        Args:
            base_url: Base URL for API calls
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.base_url = base_url.rstrip("/")


class RestProvider(RemoteProvider):
    """Base class for REST API providers."""

    name = "rest"

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
