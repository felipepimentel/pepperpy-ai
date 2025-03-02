"""Storage provider types.

This module defines the types of storage providers available.
"""

from enum import Enum, auto


class StorageProviderType(Enum):
    """Enum for storage provider types."""

    LOCAL = auto()
    CLOUD = auto()
    SQL = auto()
    MEMORY = auto()

