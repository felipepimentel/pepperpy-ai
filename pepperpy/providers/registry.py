"""Provider registry functions for PepperPy.

This module provides functions for registering and retrieving providers
in the PepperPy framework.
"""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.interfaces import ProviderConfig
from pepperpy.providers.base import BaseProvider, provider_registry


def register_provider(provider_type: str, provider_class: Type[BaseProvider]) -> None:
    """Register a provider class for a provider type.

    Args:
        provider_type: The type of the provider
        provider_class: The provider class to register

    Raises:
        ProviderError: If a provider class is already registered for the provider type
    """
    provider_registry.register(provider_type, provider_class)


def get_provider_class(provider_type: str) -> Optional[Type[BaseProvider]]:
    """Get the provider class for a provider type.

    Args:
        provider_type: The type of the provider

    Returns:
        The provider class, or None if not found
    """
    return provider_registry.get(provider_type)


def get_provider(
    provider_type: str, provider_name: Optional[str] = None, **kwargs: Any
) -> BaseProvider:
    """Create a provider instance from a provider type and settings.

    Args:
        provider_type: The type of the provider
        provider_name: Optional specific name for this provider
        **kwargs: Provider-specific configuration

    Returns:
        A provider instance

    Raises:
        ProviderError: If the provider type is not registered
    """
    return provider_registry.create(provider_type, provider_name, **kwargs)


def create_provider(config: ProviderConfig) -> BaseProvider:
    """Create a provider instance from a configuration.

    Args:
        config: The provider configuration

    Returns:
        A provider instance

    Raises:
        ProviderError: If the provider type is not registered
    """
    return get_provider(config.provider_type, None, **config.settings)


def create_provider_from_dict(
    provider_type: str, settings: Optional[Dict[str, Any]] = None
) -> BaseProvider:
    """Create a provider instance from a provider type and settings.

    Args:
        provider_type: The type of the provider
        settings: The settings for the provider

    Returns:
        A provider instance

    Raises:
        ProviderError: If the provider type is not registered
    """
    config = ProviderConfig(provider_type, settings or {})
    return create_provider(config)


def list_provider_types() -> List[str]:
    """List all registered provider types.

    Returns:
        A list of registered provider types
    """
    return provider_registry.list_types()
