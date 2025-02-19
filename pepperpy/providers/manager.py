"""Provider manager module for Pepperpy.

This module provides functionality for managing and accessing providers.
"""

from typing import Any, Dict, Optional, Type

from pepperpy.core.errors import ConfigurationError
from pepperpy.providers.base import BaseProvider, ProviderConfig
from pepperpy.providers.domain import ProviderNotFoundError


class ProviderManager:
    """Manager for provider registration and access.

    This class handles provider registration, configuration, and lifecycle
    management.
    """

    def __init__(self) -> None:
        """Initialize the provider manager."""
        self._providers: Dict[str, Type[BaseProvider]] = {}
        self._instances: Dict[str, BaseProvider] = {}

    def register_provider(
        self,
        provider_type: str,
        provider_class: Type[BaseProvider],
    ) -> None:
        """Register a provider class.

        Args:
        ----
            provider_type: Type identifier for the provider
            provider_class: Provider class to register

        Raises:
        ------
            ConfigurationError: If provider is already registered
        """
        if provider_type in self._providers:
            raise ConfigurationError(f"Provider already registered: {provider_type}")
        self._providers[provider_type] = provider_class

    async def get_provider(
        self,
        provider_type: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseProvider:
        """Get a provider instance.

        Args:
        ----
            provider_type: Type of provider to get
            config: Optional provider configuration

        Returns:
        -------
            Provider instance

        Raises:
        ------
            ProviderNotFoundError: If provider type is not found
            ConfigurationError: If provider configuration is invalid
        """
        if provider_type not in self._providers:
            raise ProviderNotFoundError(provider_type)

        if provider_type in self._instances:
            return self._instances[provider_type]

        try:
            provider_class = self._providers[provider_type]
            provider_config = ProviderConfig(**(config or {}))
            provider = provider_class(provider_config)
            await provider.initialize()
            self._instances[provider_type] = provider
            return provider
        except Exception as e:
            raise ConfigurationError(f"Failed to create provider: {e}") from e

    async def cleanup(self) -> None:
        """Clean up all provider instances."""
        for provider in self._instances.values():
            await provider.cleanup()
        self._instances.clear()
