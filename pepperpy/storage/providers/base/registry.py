"""Storage provider registry.

This module provides a registry for storage providers.
"""

from typing import Dict, Type

from pepperpy.storage.providers.base.base import BaseStorageProvider
from pepperpy.storage.providers.base.types import StorageProviderType


class StorageProviderRegistry:
    """Registry for storage providers."""

    _providers: Dict[StorageProviderType, Type[BaseStorageProvider]] = {}

    @classmethod
    def register(
        cls,
        provider_type: StorageProviderType,
        provider_class: Type[BaseStorageProvider],
    ) -> None:
        """Register a storage provider.

        Args:
            provider_type: The type of the provider.
            provider_class: The provider class.

        """
        cls._providers[provider_type] = provider_class

    @classmethod
    def get_provider(
        cls, provider_type: StorageProviderType,
    ) -> Type[BaseStorageProvider]:
        """Get a storage provider by type.

        Args:
            provider_type: The type of the provider.

        Returns:
            Type[BaseStorageProvider]: The provider class.

        Raises:
            KeyError: If the provider type is not registered.

        """
        if provider_type not in cls._providers:
            raise KeyError(f"Provider type {provider_type} not registered")
        return cls._providers[provider_type]

    @classmethod
    def list_providers(cls) -> Dict[StorageProviderType, Type[BaseStorageProvider]]:
        """List all registered providers.

        Returns:
            Dict[StorageProviderType, Type[BaseStorageProvider]]: A dictionary of provider types to provider classes.

        """
        return cls._providers.copy()
