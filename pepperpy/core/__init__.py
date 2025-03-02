"""Core functionality for PepperPy.

This module provides the core functionality and abstractions used across
the PepperPy ecosystem.
"""

from .base import BaseComponent
from .common.validation import (
    ContentValidator,
    DataValidator,
    SchemaDefinition,
    SchemaRegistry,
    ValidationError,
    Validator,
    ValidatorFactory,
)
from .registry.base import ComponentMetadata, Registry, RegistryComponent, get_registry

__all__ = [
    "BaseComponent",
    "Registry",
    "RegistryComponent",
    "ComponentMetadata",
    "get_registry",
    # Validation
    "ValidationError",
    "Validator",
    "ValidatorFactory",
    "SchemaDefinition",
    "SchemaRegistry",
    "ContentValidator",
    "DataValidator",
]
