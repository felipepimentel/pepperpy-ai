"""Registry for RAG providers.

This module provides a registry for RAG providers that can be used
to discover and instantiate providers at runtime.
"""

from typing import Dict, Optional, Type

from pepperpy.core.logging import get_logger
from pepperpy.rag.providers.base.base import RagProvider
from pepperpy.rag.providers.base.types import ProviderType

logger = get_logger(__name__)


class ProviderRegistry:
    """Registry for RAG providers."""

    _instance = None
    _providers: Dict[ProviderType, Dict[str, Type[RagProvider]]] = {}

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ProviderRegistry, cls).__new__(cls)
            for provider_type in ProviderType:
                cls._instance._providers[provider_type] = {}
        return cls._instance

    def register(
        self,
        provider_type: ProviderType,
        provider_id: str,
        provider_class: Type[RagProvider],
    ) -> None:
        """Register a provider.

        Args:
            provider_type: The type of provider
            provider_id: The unique identifier for the provider
            provider_class: The provider class to register
        """
        if provider_type not in self._providers:
            self._providers[provider_type] = {}

        self._providers[provider_type][provider_id] = provider_class
        logger.info(f"Registered {provider_type.name} provider: {provider_id}")

    def get(
        self, provider_type: ProviderType, provider_id: str
    ) -> Optional[Type[RagProvider]]:
        """Get a provider by type and ID.

        Args:
            provider_type: The type of provider
            provider_id: The unique identifier for the provider

        Returns:
            The provider class if registered, None otherwise
        """
        if provider_type not in self._providers:
            return None

        return self._providers[provider_type].get(provider_id)

    def list_providers(self, provider_type: Optional[ProviderType] = None) -> Dict:
        """List registered providers.

        Args:
            provider_type: The type of provider to list, or None for all

        Returns:
            A dictionary of registered providers
        """
        if provider_type is not None:
            return self._providers.get(provider_type, {}).copy()

        return {k: v.copy() for k, v in self._providers.items()}


# Singleton instance
provider_registry = ProviderRegistry()
