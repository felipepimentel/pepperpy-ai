"""
Base adapter interface for Pepperpy providers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from pepperpy.core.utils.errors import ProviderError
from pepperpy.providers.base.provider import Provider

T = TypeVar("T", bound=Provider)


class Adapter(Generic[T], ABC):
    """Base class for provider adapters in the Pepperpy system.

    This class provides a standardized way to adapt different provider
    implementations to work with the Pepperpy system.
    """

    def __init__(self, provider: T, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the adapter.

        Args:
            provider: The provider instance to adapt.
            config: Optional adapter configuration.
        """
        self.provider = provider
        self.config = config or {}
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Check if the adapter is initialized.

        Returns:
            True if the adapter is initialized.
        """
        return self._initialized

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter.

        This method should be called before using the adapter.
        It should handle any setup required by the adapter.

        Raises:
            ProviderError: If initialization fails.
        """
        pass

    @abstractmethod
    async def validate_config(self) -> None:
        """Validate the adapter configuration.

        This method should verify that all required configuration
        parameters are present and valid.

        Raises:
            ProviderError: If configuration is invalid.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up adapter resources.

        This method should handle any cleanup required when
        the adapter is no longer needed.

        Raises:
            ProviderError: If cleanup fails.
        """
        pass

    async def __aenter__(self) -> "Adapter[T]":
        """Async context manager entry.

        Returns:
            The adapter instance.

        Raises:
            ProviderError: If initialization fails.
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if an error occurred.
            exc_val: Exception value if an error occurred.
            exc_tb: Exception traceback if an error occurred.

        Raises:
            ProviderError: If cleanup fails.
        """
        await self.cleanup() 