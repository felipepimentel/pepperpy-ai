"""Storage module for PepperPy.

This module provides storage capabilities for saving and loading data.
"""

# Re-export public interfaces
from pepperpy.storage.public import (
    FileStorage,
    ObjectStorage,
    StorageCapability,
)

# Import internal implementations
from pepperpy.storage.base import BaseStorage, StorageError, StorageMetadata

__all__ = [
    # Public interfaces
    "StorageCapability",
    "FileStorage",
    "ObjectStorage",
    # Implementation classes
    "BaseStorage",
    "StorageError",
    "StorageMetadata",
]
