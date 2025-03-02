"""Core functionality for PepperPy.

This module provides the core functionality and abstractions used across
the PepperPy ecosystem.
"""

from .base import BaseComponent, BaseProvider
from .registry.base import ComponentMetadata, Registry, RegistryComponent, get_registry
from .types import JsonDict, JsonList, PathLike, Version
from .validation import (
    ContentValidator,
    DataValidator,
    PathValidator,
    SchemaDefinition,
    SchemaRegistry,
    ValidationError,
    ValidationManager,
    Validator,
    ValidatorFactory,
    ValidatorRegistry,
    validate_path,
)

__all__ = [
    # Base
    "BaseComponent",
    "BaseProvider",
    
    # Registry
    "Registry",
    "RegistryComponent",
    "ComponentMetadata",
    "get_registry",
    
    # Types
    "JsonDict",
    "JsonList",
    "PathLike",
    "Version",
    
    # Validation
    "ValidationError",
    "Validator",
    "ValidatorFactory",
    "ValidationManager",
    "SchemaDefinition",
    "SchemaRegistry",
    "ContentValidator",
    "DataValidator",
    "ValidatorRegistry",
    "PathValidator",
    "validate_path",
]
