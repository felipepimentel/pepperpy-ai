"""Registry for LLM providers.

This module provides a registry for LLM providers.
"""

from typing import Dict, Type

from pepperpy.llm.providers.base.base import BaseLLMProvider

# Registry of LLM provider classes
_LLM_PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {}


def register_llm_provider(name: str, provider_class: Type[BaseLLMProvider]) -> None:
    """Register an LLM provider class.

    Args:
        name: Name of the provider
        provider_class: Provider class to register

    """
    _LLM_PROVIDER_REGISTRY[name] = provider_class


def get_llm_provider(name: str) -> Type[BaseLLMProvider]:
    """Get an LLM provider class by name.

    Args:
        name: Name of the provider

    Returns:
        Type[BaseLLMProvider]: Provider class

    Raises:
        ValueError: If provider is not found

    """
    if name not in _LLM_PROVIDER_REGISTRY:
        raise ValueError(f"LLM provider '{name}' not found")
    return _LLM_PROVIDER_REGISTRY[name]


def list_llm_providers() -> list[str]:
    """List all registered LLM providers.

    Returns:
        list[str]: List of provider names

    """
    return list(_LLM_PROVIDER_REGISTRY.keys())
