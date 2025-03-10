"""Public interfaces for PepperPy Registry module.

This module provides a stable public interface for the registry functionality.
It exposes the core registry abstractions and implementations that are
considered part of the public API.
"""

from pepperpy.registry.core import (
    Component,
    ComponentId,
    ComponentMetadata,
    Registry,
    RegistryManager,
    get_registry_manager,
)

# Re-export everything
__all__ = [
    # Classes
    "Component",
    "ComponentId",
    "ComponentMetadata",
    "Registry",
    "RegistryManager",
    # Functions
    "get_registry_manager",
]
