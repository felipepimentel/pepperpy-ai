"""Provider registry for PepperPy.

This module provides functions for registering and retrieving providers
in the PepperPy framework.
"""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.interfaces import Provider, ProviderConfig
from pepperpy.providers.base import provider_registry


def register_provider(provider_type: str, provider_class: Type[Provider]) -> None:
    """Register a provider class for a provider type.

    Args:
        provider_type: The type of the provider
        provider_class: The provider class to register

    Raises:
        ValueError: If a provider class is already registered for the provider type
    """
    provider_registry.register(provider_type, provider_class)


def get_provider_class(provider_type: str) -> Optional[Type[Provider]]:
    """Get the provider class for a provider type.

    Args:
        provider_type: The type of the provider

    Returns:
        The provider class, or None if not found
    """
    return provider_registry.get(provider_type)


def create_provider(config: ProviderConfig) -> Provider:
    """Create a provider instance from a configuration.

    Args:
        config: The provider configuration

    Returns:
        A provider instance

    Raises:
        ValueError: If the provider type is not registered
    """
    return provider_registry.create(config)


def create_provider_from_dict(
    provider_type: str, settings: Optional[Dict[str, Any]] = None
) -> Provider:
    """Create a provider instance from a provider type and settings.

    Args:
        provider_type: The type of the provider
        settings: The settings for the provider

    Returns:
        A provider instance

    Raises:
        ValueError: If the provider type is not registered
    """
    config = ProviderConfig(provider_type, settings)
    return create_provider(config)


def list_provider_types() -> List[str]:
    """List all registered provider types.

    Returns:
        A list of registered provider types
    """
    return provider_registry.list_types()
