"""Core functionality for PepperPy.

This module provides the core functionality and abstractions used across
the PepperPy ecosystem.
"""

from .base import BaseComponent
from .registry.base import ComponentMetadata, Registry, RegistryComponent, get_registry
from .common.validation import (
    ValidationError,
    Validator,
    ValidatorFactory,
    SchemaDefinition,
    SchemaRegistry,
    ContentValidator,
    DataValidator,
)

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
