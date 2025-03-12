"""LLM Providers for PepperPy.

This module provides implementations of various LLM providers for the PepperPy framework.
"""

# Import registry functions directly to avoid circular imports
from pepperpy.llm.providers.registry import (
    create_provider,
    create_provider_from_dict,
    get_provider_class,
    list_provider_types,
    register_provider,
)

# Import provider implementations
from pepperpy.llm.providers.rest import (
    AnthropicProvider,
    OpenAIProvider,
    RESTLLMProvider,
)

__all__ = [
    # Registry functions
    "create_provider",
    "create_provider_from_dict",
    "get_provider_class",
    "list_provider_types",
    "register_provider",
    # Provider implementations
    "AnthropicProvider",
    "OpenAIProvider",
    "RESTLLMProvider",
]
