"""
Provider registry system for PepperPy.

This module implements a centralized registry for all providers,
allowing providers to be registered, discovered, and instantiated dynamically.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

from pepperpy.errors.core import ProviderError
from pepperpy.providers.base import BaseProvider
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


# Define ProviderNotFoundError if it doesn't exist in the errors module
class ProviderNotFoundError(ProviderError):
    """Error raised when a provider is not found in the registry."""

    pass


T = TypeVar("T", bound=BaseProvider)


class ProviderRegistry:
    """Registry for PepperPy providers.

    This class provides a central registry for all providers, allowing them
    to be registered, discovered, and instantiated dynamically.
    """

    def __init__(self) -> None:
        """Initialize a new provider registry."""
        self._providers: Dict[str, Dict[str, Type[BaseProvider]]] = {}

    def register(
        self, provider_type: str, name: str, provider_class: Type[BaseProvider]
    ) -> None:
        """Register a provider class.

        Args:
            provider_type: Provider type (e.g., "llm", "rag")
            name: Provider name
            provider_class: Provider class

        Raises:
            ValueError: If the provider is already registered
        """
        if provider_type not in self._providers:
            self._providers[provider_type] = {}

        if name in self._providers[provider_type]:
            raise ValueError(
                f"Provider '{name}' already registered for type '{provider_type}'"
            )

        self._providers[provider_type][name] = provider_class
        logger.debug(f"Registered provider '{name}' for type '{provider_type}'")

    def get_provider_class(self, provider_type: str, name: str) -> Type[BaseProvider]:
        """Get a provider class by type and name.

        Args:
            provider_type: Provider type (e.g., "llm", "rag")
            name: Provider name

        Returns:
            Provider class

        Raises:
            ProviderNotFoundError: If the provider is not found
        """
        if (
            provider_type not in self._providers
            or name not in self._providers[provider_type]
        ):
            raise ProviderNotFoundError(
                f"Provider '{name}' not found for type '{provider_type}'"
            )

        return self._providers[provider_type][name]

    def create_provider(
        self, provider_type: str, name: str, **kwargs: Any
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            provider_type: Provider type (e.g., "llm", "rag")
            name: Provider name
            **kwargs: Provider configuration

        Returns:
            Provider instance

        Raises:
            ProviderNotFoundError: If the provider is not found
        """
        provider_class = self.get_provider_class(provider_type, name)
        return provider_class.create(**kwargs)

    def list_providers(
        self, provider_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """List all registered providers.

        Args:
            provider_type: Provider type to list (optional)

        Returns:
            Dict mapping provider types to lists of provider names
        """
        if provider_type is not None:
            if provider_type not in self._providers:
                return {provider_type: []}
            return {provider_type: list(self._providers[provider_type].keys())}

        return {
            type_: list(providers.keys())
            for type_, providers in self._providers.items()
        }


# Global provider registry instance
registry = ProviderRegistry()
