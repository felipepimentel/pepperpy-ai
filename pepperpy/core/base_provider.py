"""Base Provider interfaces and implementations for PepperPy.

This module defines the base Provider interface that all providers must implement,
along with common provider functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from pepperpy.errors.core import ProviderError
from pepperpy.types import Identifiable
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for provider types
T = TypeVar("T", bound="BaseProvider")


class BaseProvider(ABC):
    """Base class for all PepperPy providers.

    A Provider is a component that connects PepperPy to external services or resources.
    All providers must implement this interface.

    Attributes:
        name: Provider name
        is_initialized: Whether the provider has been initialized
    """

    def __init__(self, name: str, **kwargs: Any) -> None:
        """Initialize a new provider.

        Args:
            name: Provider name
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self.is_initialized = False
        self._config = kwargs

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should be called before using the provider.
        It should establish any necessary connections and validate configuration.

        Raises:
            ProviderError: If initialization fails
        """
        self.is_initialized = True

    @abstractmethod
    async def close(self) -> None:
        """Close the provider and release resources.

        This method should be called when the provider is no longer needed.
        It should clean up any resources and close connections.
        """
        self.is_initialized = False

    async def __aenter__(self) -> "BaseProvider":
        """Enter async context manager."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            Dict with provider configuration
        """
        return self._config.copy()

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Dict with provider capabilities
        """
        pass

    @classmethod
    def create(cls: Type[T], **kwargs: Any) -> T:
        """Factory method to create a provider instance.

        Args:
            **kwargs: Provider configuration

        Returns:
            Provider instance
        """
        return cls(**kwargs)


class ProviderRegistry(Identifiable):
    """Registry for providers.

    The provider registry keeps track of available providers and their capabilities.
    """

    def __init__(self, registry_name: str = "provider_registry"):
        """Initialize the provider registry.

        Args:
            registry_name: The name of this registry
        """
        self._registry_name = registry_name
        self._providers: Dict[str, Type[BaseProvider]] = {}

    @property
    def id(self) -> str:
        """Get the ID of this registry.

        Returns:
            The registry ID
        """
        return self._registry_name

    def register(self, provider_type: str, provider_class: Type[BaseProvider]) -> None:
        """Register a provider class for a provider type.

        Args:
            provider_type: The type of the provider
            provider_class: The provider class to register

        Raises:
            ProviderError: If a provider class is already registered for the provider type
        """
        if provider_type in self._providers:
            raise ProviderError(
                f"Provider type '{provider_type}' is already registered"
            )
        self._providers[provider_type] = provider_class
        logger.debug(f"Registered provider type '{provider_type}'")

    def unregister(self, provider_type: str) -> None:
        """Unregister a provider type.

        Args:
            provider_type: The type of the provider to unregister

        Raises:
            ProviderError: If the provider type is not registered
        """
        if provider_type not in self._providers:
            raise ProviderError(f"Provider type '{provider_type}' is not registered")
        del self._providers[provider_type]
        logger.debug(f"Unregistered provider type '{provider_type}'")

    def get(self, provider_type: str) -> Optional[Type[BaseProvider]]:
        """Get the provider class for a provider type.

        Args:
            provider_type: The type of the provider

        Returns:
            The provider class, or None if not found
        """
        return self._providers.get(provider_type)

    def create(
        self, provider_type: str, provider_name: Optional[str] = None, **kwargs: Any
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            provider_type: The type of the provider
            provider_name: Optional specific name for this provider instance
            **kwargs: Provider-specific configuration

        Returns:
            A provider instance

        Raises:
            ProviderError: If the provider type is not registered
        """
        provider_class = self.get(provider_type)
        if provider_class is None:
            raise ProviderError(f"Provider type '{provider_type}' is not registered")
        return provider_class(
            provider_type=provider_type, provider_name=provider_name, **kwargs
        )

    def list_types(self) -> List[str]:
        """List all registered provider types.

        Returns:
            A list of registered provider types
        """
        return list(self._providers.keys())

    def clear(self) -> None:
        """Clear the registry."""
        self._providers.clear()
        logger.debug(f"Cleared registry '{self._registry_name}'")


# Global provider registry
provider_registry = ProviderRegistry()
