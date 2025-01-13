"""LLM factory module."""


from ..providers.anthropic import AnthropicConfig, AnthropicProvider
from ..providers.base import BaseProvider
from ..providers.config import ProviderConfig
from ..providers.openai import OpenAIConfig, OpenAIProvider

PROVIDER_MAP: dict[str, type[AnthropicProvider] | type[OpenAIProvider]] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}

def create_provider(
    provider_name: str,
    config: AnthropicConfig | OpenAIConfig,
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

    return provider_class(config, api_key)  # type: ignore
