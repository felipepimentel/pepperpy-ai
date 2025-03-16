"""Provider interfaces for PepperPy.

This module defines the core provider interfaces that all providers in the
PepperPy framework should implement. It provides a unified interface system
for different types of providers, such as LLM providers, storage providers,
and other service providers.

Example:
    ```python
    from pepperpy.core.providers import Provider

    class MyCustomProvider(Provider):
        def __init__(self, name: str, **kwargs):
            super().__init__(name=name, **kwargs)

        @property
        def id(self) -> str:
            return f"custom:{self.name}"

        async def initialize(self) -> None:
            # Custom initialization logic
            pass

        async def close(self) -> None:
            # Custom cleanup logic
            pass
    ```
"""

import abc
from typing import Any, Dict, Generic, Optional, Protocol, TypeVar, runtime_checkable

from pepperpy.core.base import Identifiable
from pepperpy.core.errors import (
    AuthenticationError,
    NetworkError,
    ProviderError,
    RateLimitError,
    ServerError,
    StorageError,
    TimeoutError,
)

# Type variable for provider types
T = TypeVar("T")


class Provider(Identifiable, abc.ABC):
    """Base interface for all providers in the framework.

    A provider is a component that provides specific functionality,
    such as LLM access, storage, or vector database operations.

    All providers must implement the `id` property to identify themselves,
    and should implement `initialize` and `close` methods for lifecycle
    management.
    """

    def __init__(self, name: Optional[str] = None, **kwargs: Any) -> None:
        """Initialize the provider.

        Args:
            name: Optional name for this provider instance
            **kwargs: Additional provider-specific configuration
        """
        self._name = name
        self._config = kwargs
        self._initialized = False

    @property
    def name(self) -> Optional[str]:
        """Get the name of this provider.

        Returns:
            The provider name, or None if not set
        """
        return self._name

    @property
    def config(self) -> Dict[str, Any]:
        """Get the configuration of this provider.

        Returns:
            The provider configuration
        """
        return self._config.copy()

    @property
    def is_initialized(self) -> bool:
        """Check if the provider is initialized.

        Returns:
            True if the provider is initialized, False otherwise
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        It should establish any necessary connections and validate configuration.

        Raises:
            ProviderError: If initialization fails
        """
        self._initialized = True

    async def close(self) -> None:
        """Close the provider and release any resources.

        This method should be called when the provider is no longer needed.
        The default implementation does nothing, but subclasses should override
        it if they need to release resources.
        """
        self._initialized = False

    async def __aenter__(self) -> "Provider":
        """Enter async context manager.

        Returns:
            The provider instance
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()


@runtime_checkable
class AsyncProvider(Protocol):
    """Protocol for asynchronous providers.

    This protocol defines the interface for providers that support
    asynchronous initialization and cleanup.
    """

    async def initialize(self) -> None:
        """Initialize the provider asynchronously."""
        ...

    async def close(self) -> None:
        """Close the provider asynchronously."""
        ...


class RESTProvider(Provider, abc.ABC):
    """Base class for REST API-based providers.

    This class handles common concerns for providers that interact with REST APIs,
    such as authentication, error handling, and retries.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        """Initialize the REST provider.

        Args:
            name: Optional name for this provider instance
            api_key: API key for authentication
            base_url: Base URL for API requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            **kwargs: Additional provider-specific configuration
        """
        super().__init__(name=name, **kwargs)
        self.api_key = api_key
        self.base_url = base_url or self._get_default_base_url()
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    def _get_default_base_url(self) -> str:
        """Get the default base URL for this provider.

        Returns:
            The default base URL

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _get_default_base_url")


class StorageProvider(Provider, Generic[T], abc.ABC):
    """Base class for storage providers.

    This class defines the interface for providers that store and retrieve data.

    Args:
        T: The type of data that this provider stores
    """

    @abc.abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get an item from storage.

        Args:
            key: The key of the item to get

        Returns:
            The item, or None if not found

        Raises:
            StorageError: If retrieval fails
        """
        pass

    @abc.abstractmethod
    async def set(self, key: str, value: T) -> None:
        """Set an item in storage.

        Args:
            key: The key to store the item under
            value: The item to store

        Raises:
            StorageError: If storage fails
        """
        pass

    @abc.abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete an item from storage.

        Args:
            key: The key of the item to delete

        Returns:
            True if the item was deleted, False if it didn't exist

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if an item exists in storage.

        Args:
            key: The key to check

        Returns:
            True if the item exists, False otherwise

        Raises:
            StorageError: If the check fails
        """
        pass


# Export all classes
__all__ = [
    # Base provider classes
    "Provider",
    "AsyncProvider",
    "RESTProvider",
    "StorageProvider",
    # Error classes
    "ProviderError",
    "AuthenticationError",
    "NetworkError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "StorageError",
]
