"""Provider factory module."""

from typing import Any, cast

from ..config.provider import ProviderConfig
from .anthropic import AnthropicProvider
from .base import BaseProvider
from .mock import MockProvider
from .openai import OpenAIProvider
from .openrouter import OpenRouterProvider
from .simple import SimpleProvider
from .stackspot import StackSpotProvider


def create_provider(
    name: str,
    version: str = "latest",
    api_key: str | None = None,
    api_base: str | None = None,
    api_version: str | None = None,
    organization_id: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 100,
    timeout: float = 30.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    enabled: bool = True,
    **kwargs: Any,
) -> BaseProvider:
    """Create a provider instance.

    Args:
        name: Provider name.
        version: Provider version.
        api_key: API key for authentication.
        api_base: Base URL for API requests.
        api_version: API version to use.
        organization_id: Organization ID for API requests.
        model: Default model to use.
        temperature: Default temperature for model sampling.
        max_tokens: Default maximum tokens to generate.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retries.
        retry_delay: Delay between retries in seconds.
        enabled: Whether provider is enabled.
        **kwargs: Additional provider-specific settings.

    Returns:
        A provider instance.

    Raises:
        ValueError: If provider name is invalid or if required configuration is missing.
    """
    providers: dict[str, type[BaseProvider]] = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "stackspot": StackSpotProvider,
        "simple": SimpleProvider,
        "mock": MockProvider,
    }

    if name not in providers:
        raise ValueError(
            f"Invalid provider name: {name}. "
            f"Valid providers are: {', '.join(providers.keys())}"
        )

    if api_key is None:
        raise ValueError("API key is required")

    if model is None:
        raise ValueError("Model is required")

    if api_base is None:
        api_base = ""

    provider_config = {
        "name": name,
        "version": version,
        "api_key": api_key,
        "api_base": api_base,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "max_retries": max_retries,
        "enabled": enabled,
    }
    provider_config.update(kwargs)

    config = cast(ProviderConfig, provider_config)
    provider_cls = providers[name]
    return provider_cls(config)
