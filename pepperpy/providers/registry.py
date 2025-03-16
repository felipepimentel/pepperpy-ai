"""Provider registry for PepperPy.

This module provides a registry for providers in the PepperPy framework.
It uses the core registry system to manage provider classes and instances.

Example:
    ```python
    from pepperpy.providers.registry import register_provider, create_provider
    from pepperpy.providers.custom import CustomProvider

    # Register a provider
    register_provider("custom", CustomProvider)

    # Create a provider instance
    provider = create_provider("custom", api_key="your-api-key")

    # Use the provider
    response = provider.process("Hello, world!")
    ```
"""

from typing import Any, Dict, List, Optional, Type

from pepperpy.core.registry import ProviderRegistry
from pepperpy.providers.base import BaseProvider

# Provider registry
provider_registry = ProviderRegistry[BaseProvider](
    registry_name="provider_registry", registry_type="provider"
)


def register_provider(
    provider_type: str, name: str, provider_class: Type[BaseProvider]
) -> None:
    """Register a provider class.

    Args:
        provider_type: The type of the provider (e.g., "storage", "vector_db")
        name: The name of the provider
        provider_class: The provider class to register

    Raises:
        RegistryError: If a provider with the same name is already registered
    """
    provider_registry.register_provider(provider_type, name, provider_class)


def get_provider_class(provider_type: str, name: str) -> Type[BaseProvider]:
    """Get a provider class.

    Args:
        provider_type: The type of the provider
        name: The name of the provider

    Returns:
        The provider class

    Raises:
        RegistryError: If the provider is not found
    """
    return provider_registry.get_provider_class(provider_type, name)


def get_provider(provider_type: str, name: str, **kwargs: Any) -> BaseProvider:
    """Get a provider instance.

    Args:
        provider_type: The type of the provider
        name: The name of the provider
        **kwargs: Provider-specific configuration

    Returns:
        A provider instance

    Raises:
        RegistryError: If the provider is not found or creation fails
    """
    return provider_registry.create_provider(provider_type, name, **kwargs)


def create_provider(provider_type: str, name: str, **kwargs: Any) -> BaseProvider:
    """Create a provider instance.

    Args:
        provider_type: The type of the provider
        name: The name of the provider
        **kwargs: Provider-specific configuration

    Returns:
        A provider instance

    Raises:
        RegistryError: If the provider is not found or creation fails
    """
    return provider_registry.create_provider(provider_type, name, **kwargs)


def create_provider_from_dict(
    provider_type: str, name: str, settings: Dict[str, Any]
) -> BaseProvider:
    """Create a provider instance from a dictionary.

    Args:
        provider_type: The type of the provider
        name: The name of the provider
        settings: Provider-specific configuration

    Returns:
        A provider instance

    Raises:
        RegistryError: If the provider is not found or creation fails
    """
    return create_provider(provider_type, name, **settings)


def list_provider_types() -> List[str]:
    """List all registered provider types.

    Returns:
        A list of registered provider types
    """
    return list(provider_registry.list_providers().keys())


def list_providers(provider_type: Optional[str] = None) -> Dict[str, List[str]]:
    """List all registered providers.

    Args:
        provider_type: Optional provider type to filter by

    Returns:
        A dictionary mapping provider types to lists of provider names
    """
    return provider_registry.list_providers(provider_type)


__all__ = [
    "provider_registry",
    "register_provider",
    "get_provider_class",
    "get_provider",
    "create_provider",
    "create_provider_from_dict",
    "list_provider_types",
    "list_providers",
]
