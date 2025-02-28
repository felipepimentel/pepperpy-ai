"""Core functionality for PepperPy.

This module provides the core functionality and abstractions used across
the PepperPy ecosystem.
"""

from .base import BaseComponent
from .registry.base import Registry, RegistryComponent, ComponentMetadata, get_registry

__all__ = [
    "BaseComponent",
    "Registry",
    "RegistryComponent",
    "ComponentMetadata",
    "get_registry",
]
