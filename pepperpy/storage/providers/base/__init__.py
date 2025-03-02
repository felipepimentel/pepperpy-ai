"""Base module for storage providers.

This module provides base classes and interfaces for storage providers.
"""

from pepperpy.storage.providers.base.base import BaseStorageProvider
from pepperpy.storage.providers.base.registry import StorageProviderRegistry
from pepperpy.storage.providers.base.types import StorageProviderType

__all__ = ["BaseStorageProvider", "StorageProviderRegistry", "StorageProviderType"]
