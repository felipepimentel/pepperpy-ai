"""
Storage Module.

This module provides interfaces and implementations for data storage and retrieval
in PepperPy. It handles persistent data storage with various provider backends.
"""

from pepperpy.storage.provider import (
    StorageConfig,
    StorageConnection,
    StorageContainer,
    StorageError,
    StorageObject,
    StorageProvider,
    StorageQuery,
    StorageResult,
)

__all__ = [
    # Core interfaces
    "StorageProvider",
    "StorageConfig",
    "StorageError",
    "StorageConnection",
    "StorageObject",
    "StorageContainer",
    "StorageQuery",
    "StorageResult",
]
