"""LLM Providers Module.

This module defines the provider interfaces and implementations for various LLM
services. Each provider implements a common interface that allows for
standardized access to different LLM backends.

Available providers:
- OpenAI
- Anthropic
- Local (for testing and development)

Example:
    ```python
    from pepperpy.llm.providers import create_provider

    # Create an OpenAI provider with API key
    provider = create_provider("openai", api_key="sk-...")

    # Generate text
    result = await provider.generate("Tell me a joke about AI")
    ```
"""

from typing import Any, Dict, Type

from pepperpy.core.errors import NotFoundError
from pepperpy.llm.providers.base import LLMProvider

# Registry of available providers
_PROVIDERS: Dict[str, Type[LLMProvider]] = {}


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """Register a provider implementation.

    Args:
        name: The name of the provider to register
        provider_class: The provider class to register
    """
    _PROVIDERS[name.lower()] = provider_class


def create_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Create a provider instance.

    Args:
        provider_name: The name of the provider to create
        **kwargs: Additional arguments to pass to the provider constructor

    Returns:
        An instance of the specified provider

    Raises:
        NotFoundError: If the specified provider is not registered
    """
    provider_name = provider_name.lower()

    if provider_name not in _PROVIDERS:
        raise NotFoundError(
            f"Provider '{provider_name}' not found. Available providers: {list(_PROVIDERS.keys())}"
        )

    provider_class = _PROVIDERS[provider_name]
    return provider_class(**kwargs)


def get_available_providers() -> list[str]:
    """Get the names of all available providers.

    Returns:
        A list of provider names
    """
    return list(_PROVIDERS.keys())


# Import the provider classes
from pepperpy.llm.providers.local.provider import LocalProvider
from pepperpy.llm.providers.rest import AnthropicProvider, OpenAIProvider

# Register providers
register_provider("openai", OpenAIProvider)
register_provider("anthropic", AnthropicProvider)
register_provider("local", LocalProvider)

# Public APIs
__all__ = [
    "LLMProvider",
    "create_provider",
    "register_provider",
    "get_available_providers",
    "OpenAIProvider",
    "AnthropicProvider",
    "LocalProvider",
]
