"""Common module for Pepperpy."""

from .errors import PepperpyError
from .types.data import Mergeable, Versionable
from .types.base import (
    PepperpyObject,
    DictInitializable,
    Cloneable,
    Validatable,
    Serializable,
    Equatable,
    Comparable,
    Stringable,
    ContextManageable,
    Disposable,
)
from .base import (
    Component,
    BaseConfig,
)
from .registry import (
    Factory,
    Registry,
)

__all__ = [
    # Errors
    "PepperpyError",
    
    # Common protocols
    "Mergeable",
    "Versionable",
    
    # Base types
    "PepperpyObject",
    "DictInitializable",
    "Cloneable",
    "Validatable",
    "Serializable",
    "Equatable",
    "Comparable",
    "Stringable",
    "ContextManageable",
    "Disposable",
    
    # Base components
    "Component",
    "BaseConfig",
    "Factory",
    "Registry",
]
