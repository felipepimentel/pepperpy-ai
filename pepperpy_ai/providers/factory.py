"""Provider factory module."""

from typing import Type, cast

from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .openrouter import OpenRouterProvider
from .mock import MockProvider
from .base import BaseProvider
from .config import ProviderConfig

PROVIDER_MAP: dict[str, Type[BaseProvider[ProviderConfig]]] = {
    "anthropic": cast(Type[BaseProvider[ProviderConfig]], AnthropicProvider),
    "openai": cast(Type[BaseProvider[ProviderConfig]], OpenAIProvider),
    "openrouter": cast(Type[BaseProvider[ProviderConfig]], OpenRouterProvider),
    "mock": cast(Type[BaseProvider[ProviderConfig]], MockProvider),
}

def create_provider(
    provider_name: str,
    config: ProviderConfig,
    api_key: str,
) -> BaseProvider[ProviderConfig]:
    """Create a provider instance.

    Args:
        provider_name: Name of the provider to create
        config: Provider configuration
        api_key: API key for the provider

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported
    """
    provider_class = PROVIDER_MAP.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unsupported provider: {provider_name}")

    return provider_class(config, api_key)
