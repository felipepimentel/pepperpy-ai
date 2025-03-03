"""Base interfaces and exceptions for storage providers.

This module provides base classes and utilities for storage implementations.
"""


# Define StorageMetadata type
class StorageMetadata(dict):
    """Metadata for storage items."""



class StorageError(Exception):
    """Base exception for storage errors."""



# Define a base storage class
class BaseStorage:
    """Base class for storage implementations."""

    def __init__(self, name: str):
        """Initialize storage.

        Args:
            name: Storage name

        """
        self.name = name


# Export the interfaces
__all__ = ["BaseStorage", "StorageError", "StorageMetadata"]
