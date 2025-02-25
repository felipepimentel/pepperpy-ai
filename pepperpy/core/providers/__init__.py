"""Core provider system.

This module provides the core provider system for the Pepperpy framework.
It includes interfaces and base classes for implementing providers.
"""

from pepperpy.core.providers.unified import (
    BaseProvider,
    ProviderConfig,
    ProviderError,
    ProviderNotFoundError,
    UnifiedProviderRegistry,
    get_registry,
)

__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "ProviderError",
    "ProviderNotFoundError",
    "UnifiedProviderRegistry",
    "get_registry",
]
"""Provider management and interfaces.

This package provides provider management and interfaces for the
Pepperpy framework. It includes:
- Base provider interface
- Provider configuration
- Provider management
- Error handling

Example:
    >>> from pepperpy.core.providers import BaseProvider, ProviderManager
    >>> manager = ProviderManager()
    >>> manager.register_provider("my_provider", MyProvider)
    >>> provider = await manager.get_provider("my_provider")
"""

from pepperpy.core.providers.base import BaseProvider, ProviderConfig
from pepperpy.core.providers.errors import (
    ProviderConfigurationError,
    ProviderError,
    ProviderNotFoundError,
    ProviderResourceError,
    ProviderRuntimeError,
)
from pepperpy.core.providers.manager import ProviderManager

__all__ = [
    "BaseProvider",
    "ProviderConfig",
    "ProviderConfigurationError",
    "ProviderError",
    "ProviderManager",
    "ProviderNotFoundError",
    "ProviderResourceError",
    "ProviderRuntimeError",
]
