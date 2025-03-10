"""Core provider functionality for Language Models.

This module defines the core abstractions and implementations for LLM providers.
It provides a registry of available providers and a factory function to create them.
"""

from typing import Any, Dict, Optional, Type

from pepperpy.llm.core import LLMProviderBase

# Registry of available providers
_PROVIDER_REGISTRY: Dict[str, Type[LLMProviderBase]] = {}


def register_provider(
    provider_type: str, provider_class: Type[LLMProviderBase]
) -> None:
    """Register an LLM provider.

    Args:
        provider_type: The type of provider to register
        provider_class: The provider class to register
    """
    _PROVIDER_REGISTRY[provider_type] = provider_class


def get_provider_class(provider_type: str) -> Optional[Type[LLMProviderBase]]:
    """Get an LLM provider class.

    Args:
        provider_type: The type of provider to get

    Returns:
        The provider class, or None if not found
    """
    return _PROVIDER_REGISTRY.get(provider_type)


def create_provider(provider_type: str, **kwargs: Any) -> LLMProviderBase:
    """Create an LLM provider.

    Args:
        provider_type: The type of provider to create
        **kwargs: Provider-specific configuration

    Returns:
        The created provider

    Raises:
        ValueError: If the provider type is not supported
    """
    provider_class = get_provider_class(provider_type)
    if not provider_class:
        raise ValueError(f"Unsupported provider type: {provider_type}")

    return provider_class(**kwargs)


# Import and register built-in providers
def _register_builtin_providers() -> None:
    """Register built-in providers.

    This function attempts to import and register all built-in providers.
    If a provider is not available (e.g., due to missing dependencies),
    it will be skipped.

    Note: This function is commented out to avoid linter errors.
    It will be uncommented when the actual provider implementations are available.
    """
    pass
    """
    # These imports are handled with try/except to avoid hard dependencies
    # on specific provider libraries
    
    # OpenAI provider
    try:
        # This import will be resolved when the actual provider is implemented
        # For now, we'll just catch the ImportError
        from pepperpy.llm.providers.openai import OpenAIProvider
        register_provider("openai", OpenAIProvider)
    except (ImportError, AttributeError):
        # Either the module doesn't exist or the class doesn't exist
        pass
    
    # Anthropic provider
    try:
        # This import will be resolved when the actual provider is implemented
        from pepperpy.llm.providers.anthropic import AnthropicProvider
        register_provider("anthropic", AnthropicProvider)
    except (ImportError, AttributeError):
        pass
    
    # Gemini provider
    try:
        # This import will be resolved when the actual provider is implemented
        from pepperpy.llm.providers.gemini import GeminiProvider
        register_provider("gemini", GeminiProvider)
    except (ImportError, AttributeError):
        pass
    
    # Perplexity provider
    try:
        # This import will be resolved when the actual provider is implemented
        from pepperpy.llm.providers.perplexity import PerplexityProvider
        register_provider("perplexity", PerplexityProvider)
    except (ImportError, AttributeError):
        pass
    
    # OpenRouter provider
    try:
        # This import will be resolved when the actual provider is implemented
        from pepperpy.llm.providers.openrouter import OpenRouterProvider
        register_provider("openrouter", OpenRouterProvider)
    except (ImportError, AttributeError):
        pass
    """


# Register built-in providers
# This is commented out for now to avoid linter errors
# _register_builtin_providers()
