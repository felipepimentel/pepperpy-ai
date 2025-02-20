"""Storage module for the Pepperpy Hub.

This module provides storage functionality for the Hub, including:
- Base storage interfaces and metadata types
- Local file system storage backend
"""

from pepperpy.hub.storage.base import StorageBackend, StorageMetadata
from pepperpy.hub.storage.local import LocalStorageBackend

__all__ = ["StorageBackend", "StorageMetadata", "LocalStorageBackend"]
