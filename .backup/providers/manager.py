"""Provider manager module for Pepperpy.

This module provides functionality to manage and access different providers.
"""

from typing import Dict, Type

from pepperpy.providers.base import Provider, ProviderConfig
from pepperpy.providers.domain import ProviderNotFoundError
from pepperpy.providers.services.openai import OpenAIProvider
from pepperpy.providers.services.openrouter import OpenRouterProvider


class ProviderManager:
    """Manages provider instances and their configurations."""

    def __init__(self):
        self._providers: Dict[str, Provider] = {}
        self._provider_classes: Dict[str, Type[Provider]] = {
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
        }

    def get_provider(self, name: str) -> Provider:
        """Get a provider instance by name."""
        if name not in self._providers:
            raise ProviderNotFoundError(f"Provider '{name}' not found")
        return self._providers[name]

    def register_provider(self, config: ProviderConfig) -> None:
        """Register and initialize a new provider."""
        if config.name not in self._provider_classes:
            raise ProviderNotFoundError(f"Provider class for '{config.name}' not found")

        provider_class = self._provider_classes[config.name]
        provider = provider_class()
        provider.initialize(config)
        self._providers[config.name] = provider

    def cleanup(self) -> None:
        """Clean up all provider instances."""
        for provider in self._providers.values():
            provider.cleanup()
        self._providers.clear()
