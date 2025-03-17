"""PepperPy Providers Module.

This module provides components for integrating with external services and APIs,
including base provider classes and registry functionality.
"""

from pepperpy.core.registry import ProviderRegistry
from pepperpy.providers.base import (
    AsyncProvider,
    BaseProvider,
    CustomRateLimitError,
    Provider,
    ProviderError,
    RESTProvider,
    StorageProvider,
    retry,
)
from pepperpy.providers.registry import (
    create_provider,
    create_provider_from_dict,
    get_provider,
    get_provider_class,
    list_provider_types,
    list_providers,
    provider_registry,
    register_provider,
)

__all__ = [
    # Base classes and interfaces
    "AsyncProvider",
    "BaseProvider",
    "Provider",
    "ProviderError",
    "ProviderRegistry",
    "RESTProvider",
    "StorageProvider",
    # Custom errors
    "CustomRateLimitError",
    # Global instances
    "provider_registry",
    # Registry functions
    "create_provider",
    "create_provider_from_dict",
    "get_provider",
    "get_provider_class",
    "list_provider_types",
    "list_providers",
    "register_provider",
    # Utilities
    "retry",
]
