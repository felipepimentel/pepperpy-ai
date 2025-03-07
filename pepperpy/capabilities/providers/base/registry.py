"""Provider registry.

This module provides a registry for provider capabilities.
"""

from typing import Dict, Optional, Type

from pepperpy.capabilities.providers.base.base import ProviderCapability


class ProviderRegistry:
    """Registry for provider capabilities."""

    _providers: Dict[str, Type[ProviderCapability]] = {}

    @classmethod
    def register(
        cls, provider_type: str, provider_class: Type[ProviderCapability]
    ) -> None:
        """Register a provider.

        Args:
            provider_type: Provider type identifier
            provider_class: Provider class
        """
        cls._providers[provider_type] = provider_class

    @classmethod
    def get(cls, provider_type: str) -> Optional[Type[ProviderCapability]]:
        """Get a provider by type.

        Args:
            provider_type: Provider type identifier

        Returns:
            Provider class or None if not found
        """
        return cls._providers.get(provider_type)

    @classmethod
    def list_providers(cls) -> Dict[str, Type[ProviderCapability]]:
        """List all registered providers.

        Returns:
            Dictionary mapping provider types to provider classes
        """
        return cls._providers.copy()
