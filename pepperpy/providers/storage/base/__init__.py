"""Base module for storage providers.

This module provides base classes and interfaces for storage providers.
"""

from pepperpy.providers.storage.base.base import BaseStorageProvider
from pepperpy.providers.storage.base.registry import StorageProviderRegistry
from pepperpy.providers.storage.base.types import StorageProviderType

__all__ = ["BaseStorageProvider", "StorageProviderRegistry", "StorageProviderType"]
