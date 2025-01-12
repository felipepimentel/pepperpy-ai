"""Provider factory module."""

from typing import cast

from .anthropic import AnthropicProvider
from .base import BaseProvider
from .config import ProviderConfig
from .mock import MockProvider
from .openai import OpenAIProvider
from .openrouter import OpenRouterProvider

PROVIDER_MAP: dict[str, type[BaseProvider[ProviderConfig]]] = {
    "anthropic": cast(type[BaseProvider[ProviderConfig]], AnthropicProvider),
    "openai": cast(type[BaseProvider[ProviderConfig]], OpenAIProvider),
    "openrouter": cast(type[BaseProvider[ProviderConfig]], OpenRouterProvider),
    "mock": cast(type[BaseProvider[ProviderConfig]], MockProvider),
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
