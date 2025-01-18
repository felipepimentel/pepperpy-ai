"""Provider module for LLM interactions."""

from typing import Any

from pepperpy.providers.base import LLMProvider
from pepperpy.providers.openai import OpenAIProvider

# Default provider mapping
PROVIDERS = {
    "openai": OpenAIProvider,
}


async def create_provider(provider: str, **config: Any) -> LLMProvider:
    """Create and initialize a provider.

    Args:
        provider: Provider type ("openai", etc)
        **config: Provider-specific configuration

    Returns:
        Initialized provider instance

    Raises:
        ValueError: If provider type is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Available providers: {list(PROVIDERS.keys())}"
        )

    provider_class = PROVIDERS[provider]
    instance = provider_class()
    await instance.initialize(**config)
    return instance


__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "create_provider",
]
