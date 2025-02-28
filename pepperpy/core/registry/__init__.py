"""Unified Registry System

This package provides a unified registry system for PepperPy components.
It implements a central registry mechanism that can be used by all modules
to register and discover components in a consistent way.
"""

from pepperpy.common.registry.base import (
    ComponentDuplicateError,
    ComponentMetadata,
    ComponentNotFoundError,
    Registry,
    RegistryComponent,
    RegistryError,
    auto_register,
    get_registry,
)

__all__ = [
    "Registry",
    "RegistryComponent",
    "ComponentMetadata",
    "RegistryError",
    "ComponentNotFoundError",
    "ComponentDuplicateError",
    "get_registry",
    "auto_register",
]
