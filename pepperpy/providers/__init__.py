"""Provider package for the Pepperpy framework.

This package provides a unified interface for interacting with various
AI providers (e.g., OpenAI, Gemini). It handles provider initialization,
configuration, and error handling.

Basic Usage:
    >>> from pepperpy.providers import create_provider
    >>> provider = create_provider("openai", api_key="...")
    >>> response = await provider.complete("Hello, world!")
    >>> print(response)

Advanced Usage:
    >>> from pepperpy.providers import Provider, ProviderConfig
    >>> config = ProviderConfig(
    ...     provider_type="openai",
    ...     api_key="your-api-key",
    ...     model="gpt-4",
    ...     timeout=30.0
    ... )
    >>> async with Provider(config) as provider:
    ...     response = await provider.complete(
    ...         "Tell me a story",
    ...         temperature=0.7,
    ...         max_tokens=100
    ...     )
    ...     print(response)
"""

from typing import Any

from .domain import (
    Conversation,
    Message,
    ProviderAPIError,
    ProviderConfigError,
    ProviderError,
    ProviderInitError,
    ProviderNotFoundError,
    ProviderRateLimitError,
)
from .engine import create_provider, list_providers
from .provider import Provider, ProviderConfig

__all__ = [
    "Conversation",
    "Message",
    "Provider",
    "ProviderAPIError",
    "ProviderConfig",
    "ProviderConfigError",
    "ProviderError",
    "ProviderInitError",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "create_provider",
    "list_providers",
]

# Version information
__version__ = "1.0.0"
__author__ = "Pepperpy Team"
