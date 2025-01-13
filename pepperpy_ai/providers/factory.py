"""Provider factory module."""

from typing import cast

from .anthropic import AnthropicProvider
from .base import BaseProvider
from .config import ProviderConfig, ProviderSettings
from .exceptions import ProviderError
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
    settings: ProviderSettings | None = None,
    prefix: str = "",
) -> BaseProvider[ProviderConfig]:
    """Create a provider instance.

    If settings is not provided, they will be loaded from environment variables.
    Environment variables are prefixed with the given prefix.

    Args:
        settings: Provider settings
        prefix: Environment variable prefix (e.g., "PEPPERPY_")

    Returns:
        Provider instance

    Raises:
        ProviderError: If provider is not supported or configuration is invalid
    """
    # Load settings from environment if not provided
    if settings is None:
        settings = ProviderSettings.from_env(prefix)

    # Get provider class
    provider_class = PROVIDER_MAP.get(settings.name)
    if not provider_class:
        raise ProviderError(
            f"Unsupported provider: {settings.name}",
            provider=settings.name,
            operation="create",
        )

    # Cast config to correct type
    config = cast(ProviderConfig, settings.config)
    return provider_class(config, settings.api_key)
