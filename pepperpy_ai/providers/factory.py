"""Provider factory module."""

import os
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


def load_settings_from_env(prefix: str = "") -> ProviderSettings:
    """Load provider settings from environment variables.

    Args:
        prefix: Environment variable prefix (e.g., "PEPPERPY_")

    Returns:
        Provider settings

    Raises:
        ProviderError: If required environment variables are not set
    """
    provider = os.getenv(f"{prefix}PROVIDER")
    if not provider:
        raise ProviderError(
            f"Provider not set in environment ({prefix}PROVIDER)",
            provider="unknown",
            operation="load_settings",
        )

    api_key = os.getenv(f"{prefix}API_KEY")
    if not api_key:
        raise ProviderError(
            f"API key not set in environment ({prefix}API_KEY)",
            provider=provider,
            operation="load_settings",
        )

    settings: ProviderSettings = {
        "api_key": api_key,
        "timeout": float(os.getenv(f"{prefix}TIMEOUT", "30.0")),
        "max_retries": int(os.getenv(f"{prefix}MAX_RETRIES", "3")),
        "retry_delay": float(os.getenv(f"{prefix}RETRY_DELAY", "1.0")),
    }

    # Add optional settings if present
    api_base = os.getenv(f"{prefix}API_BASE")
    if api_base:
        settings["api_base"] = api_base

    model = os.getenv(f"{prefix}MODEL")
    if model:
        settings["model"] = model

    return settings


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
        settings = load_settings_from_env(prefix)

    # Get provider class
    provider = os.getenv(f"{prefix}PROVIDER")
    if not provider:
        raise ProviderError(
            f"Provider not set in environment ({prefix}PROVIDER)",
            provider="unknown",
            operation="create",
        )

    provider_class = PROVIDER_MAP.get(provider)
    if not provider_class:
        raise ProviderError(
            f"Unsupported provider: {provider}",
            provider=provider,
            operation="create",
        )

    # Create provider config
    config = ProviderConfig(
        name=provider,
        version="1.0.0",
        settings=settings,
    )

    api_key = settings.get("api_key")
    if not api_key:
        raise ProviderError(
            "API key not specified in settings",
            provider=provider,
            operation="create",
        )

    return provider_class(config, api_key)
