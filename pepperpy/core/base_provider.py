"""Base provider functionality for PepperPy.

This module provides the base functionality for providers in PepperPy.
Providers are responsible for implementing specific services or integrations,
such as LLM models, storage backends, or external APIs.
"""

import abc
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from pepperpy.errors.core import ProviderError
from pepperpy.types import Identifiable
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for provider types
T = TypeVar("T")


class BaseProvider(abc.ABC):
    """Base class for all providers in the framework.

    This class provides common functionality that all providers should implement,
    including configuration, capability management, and validation.
    """

    def __init__(
        self,
        provider_type: str,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs: Any,
    ):
        """Initialize the provider.

        Args:
            provider_type: The type of this provider
            provider_name: Optional specific name for this provider
            model_name: Optional model name used by this provider
            **kwargs: Provider-specific configuration
        """
        self.provider_type = provider_type
        self.provider_name = provider_name or self.__class__.__name__
        self.model_name = model_name
        self.config = kwargs
        self._capabilities: Set[str] = set()

    def add_capability(self, capability: str) -> None:
        """Add a capability to the provider.

        Args:
            capability: The capability to add
        """
        self._capabilities.add(capability)

    def has_capability(self, capability: str) -> bool:
        """Check if the provider has a capability.

        Args:
            capability: The name of the capability to check

        Returns:
            True if the provider has the capability, False otherwise
        """
        return capability in self._capabilities

    def get_capabilities(self) -> Set[str]:
        """Get the capabilities of the provider.

        Returns:
            The set of capability names
        """
        return self._capabilities.copy()

    async def validate(self) -> None:
        """Validate the provider configuration.

        This method should be overridden by subclasses to perform
        provider-specific validation.

        Raises:
            ProviderError: If the provider configuration is invalid
        """
        # Default implementation does nothing
        pass

    async def initialize(self) -> None:
        """Initialize the provider.

        This method is called when the provider is first used.
        It should establish any necessary connections or resources.

        Raises:
            ProviderError: If the provider initialization fails
        """
        # Default implementation does nothing
        pass

    async def close(self) -> None:
        """Close the provider and release resources.

        This method is called when the provider is no longer needed.
        It should release any resources used by the provider.

        Raises:
            ProviderError: If the provider close fails
        """
        # Default implementation does nothing
        pass

    def __repr__(self) -> str:
        """Get a string representation of the provider.

        Returns:
            A string representation
        """
        type_str = f"type='{self.provider_type}'"
        name_str = f", name='{self.provider_name}'" if self.provider_name else ""
        model_str = f", model='{self.model_name}'" if self.model_name else ""
        return f"{self.__class__.__name__}({type_str}{name_str}{model_str})"


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
