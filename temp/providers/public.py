"""Public interfaces for PepperPy Providers module.

This module provides a stable public interface for the providers functionality.
It exposes the core provider abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.core.interfaces import Provider, ProviderCapability, ProviderConfig
from pepperpy.providers.base import BaseProvider
from pepperpy.providers.registry import (
    create_provider,
    create_provider_from_dict,
    get_provider_class,
    list_provider_types,
    register_provider,
)

# Re-export everything
__all__ = [
    # Classes
    "BaseProvider",
    "Provider",
    "ProviderCapability",
    "ProviderConfig",
    # Functions
    "create_provider",
    "create_provider_from_dict",
    "get_provider_class",
    "list_provider_types",
    "register_provider",
]
