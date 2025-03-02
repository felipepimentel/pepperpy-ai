"""Base interfaces and exceptions for storage providers.

This module re-exports the storage interfaces from pepperpy.interfaces.storage
and provides additional types and utilities for storage implementations.
"""

# Import the base interfaces
from pepperpy.interfaces.storage import StorageError, StorageProvider


# Define StorageMetadata type
class StorageMetadata(dict):
    """Metadata for storage items."""

    pass


# Re-export the interfaces
__all__ = ["StorageError", "StorageProvider", "StorageMetadata"]

# Note: The actual implementation of StorageProvider should be in the
# provider-specific modules that inherit from the interface defined in
# pepperpy.interfaces.storage.
