"""Base classes for providers in PepperPy.

This module defines the base classes for providers in the PepperPy framework.
Providers are responsible for integrating with external services and APIs.
"""

from typing import Any, Dict, List, Optional, Set, Type

from pepperpy.core.interfaces import Provider, ProviderCapability, ProviderConfig


class ProviderRegistry:
    """Registry for providers.

    The provider registry keeps track of available provider types and their
    implementations.
    """

    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[str, Type[Provider]] = {}

    def register(self, provider_type: str, provider_class: Type[Provider]) -> None:
        """Register a provider class for a provider type.

        Args:
            provider_type: The type of the provider
            provider_class: The provider class to register

        Raises:
            ValueError: If a provider class is already registered for the provider type
        """
        if provider_type in self._providers:
            raise ValueError(f"Provider type '{provider_type}' is already registered")
        self._providers[provider_type] = provider_class

    def get(self, provider_type: str) -> Optional[Type[Provider]]:
        """Get the provider class for a provider type.

        Args:
            provider_type: The type of the provider

        Returns:
            The provider class, or None if not found
        """
        return self._providers.get(provider_type)

    def create(self, config: ProviderConfig) -> Provider:
        """Create a provider instance from a configuration.

        Args:
            config: The provider configuration

        Returns:
            A provider instance

        Raises:
            ValueError: If the provider type is not registered
        """
        provider_class = self.get(config.provider_type)
        if provider_class is None:
            raise ValueError(
                f"Provider type '{config.provider_type}' is not registered"
            )
        return provider_class(**config.settings)

    def list_types(self) -> List[str]:
        """List all registered provider types.

        Returns:
            A list of registered provider types
        """
        return list(self._providers.keys())


class BaseProvider(Provider):
    """Base class for all providers.

    This class provides common functionality for all providers, including
    capability management and validation.
    """

    def __init__(self, **kwargs: Any):
        """Initialize the provider.

        Args:
            **kwargs: Provider-specific configuration
        """
        self.config = kwargs
        self._capabilities: Set[str] = set()

    def add_capability(self, capability: ProviderCapability) -> None:
        """Add a capability to the provider.

        Args:
            capability: The capability to add
        """
        self._capabilities.add(capability.name)

    def has_capability(self, capability_name: str) -> bool:
        """Check if the provider has a capability.

        Args:
            capability_name: The name of the capability to check

        Returns:
            True if the provider has the capability, False otherwise
        """
        return capability_name in self._capabilities

    def get_capabilities(self) -> Set[str]:
        """Get the capabilities of the provider.

        Returns:
            The set of capability names
        """
        return self._capabilities.copy()

    async def validate(self) -> None:
        """Validate the provider.

        This method should be overridden by subclasses to perform
        provider-specific validation.

        Raises:
            ValueError: If the provider is not properly configured
        """
        # Default implementation does nothing
        pass


# Global provider registry
provider_registry = ProviderRegistry()
