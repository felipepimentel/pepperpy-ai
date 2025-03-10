"""Registry for LLM providers in PepperPy.

This module provides functions for registering and retrieving LLM providers
in the PepperPy framework.
"""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.interfaces import ProviderConfig
from pepperpy.llm.core import LLMProviderBase

# Dictionary to store registered LLM providers
_llm_providers: Dict[str, Type[LLMProviderBase]] = {}


def register_provider(
    provider_type: str, provider_class: Type[LLMProviderBase]
) -> None:
    """Register an LLM provider class for a provider type.

    Args:
        provider_type: The type of the provider
        provider_class: The provider class to register

    Raises:
        ValueError: If a provider class is already registered for the provider type
    """
    if provider_type in _llm_providers:
        raise ValueError(f"Provider type '{provider_type}' is already registered")
    _llm_providers[provider_type] = provider_class


def get_provider_class(provider_type: str) -> Optional[Type[LLMProviderBase]]:
    """Get the LLM provider class for a provider type.

    Args:
        provider_type: The type of the provider

    Returns:
        The provider class, or None if not found
    """
    return _llm_providers.get(provider_type)


def create_provider(config: ProviderConfig) -> LLMProviderBase:
    """Create an LLM provider instance from a configuration.

    Args:
        config: The provider configuration

    Returns:
        An LLM provider instance

    Raises:
        ValueError: If the provider type is not registered
    """
    provider_class = get_provider_class(config.provider_type)
    if provider_class is None:
        raise ValueError(f"Provider type '{config.provider_type}' is not registered")
    return provider_class(**config.settings)


def create_provider_from_dict(
    provider_type: str, settings: Optional[Dict[str, Any]] = None
) -> LLMProviderBase:
    """Create an LLM provider instance from a provider type and settings.

    Args:
        provider_type: The type of the provider
        settings: The settings for the provider

    Returns:
        An LLM provider instance

    Raises:
        ValueError: If the provider type is not registered
    """
    config = ProviderConfig(provider_type, settings or {})
    return create_provider(config)


def list_provider_types() -> List[str]:
    """List all registered LLM provider types.

    Returns:
        A list of registered provider types
    """
    return list(_llm_providers.keys())
