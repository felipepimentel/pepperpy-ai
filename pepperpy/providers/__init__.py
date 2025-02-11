"""Providers package for AI model interactions.

This package provides base classes and implementations for different AI providers.
"""

from typing import Dict, Type

from pepperpy.monitoring import logger as logger
from pepperpy.providers.base import BaseProvider, Provider, ProviderConfig
from pepperpy.providers.openai import OpenAIProvider
from pepperpy.providers.services.openrouter import OpenRouterProvider

# Registry of available providers
PROVIDERS: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "openrouter": OpenRouterProvider,
}


def get_provider(
    provider_name: str, config: ProviderConfig | None = None
) -> BaseProvider:
    """Get a provider instance by name.

    Args:
    ----
        provider_name: Name of the provider to get
        config: Optional provider configuration

    Returns:
    -------
        An instance of the provider

    Raises:
    ------
        ValueError: If the provider is not found

    """
    if provider_name not in PROVIDERS:
        raise ValueError(f"Provider '{provider_name}' not found")

    provider_class = PROVIDERS[provider_name]
    return provider_class(config or ProviderConfig())


__all__ = ["Provider"]
