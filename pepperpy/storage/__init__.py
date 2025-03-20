"""Storage capabilities for PepperPy.

This module provides interfaces and implementations for working with
storage systems, including local and cloud-based providers.

Example:
    >>> from pepperpy.storage import StorageProvider
    >>> provider = StorageProvider.from_config({
    ...     "provider": "local",
    ...     "root_dir": "/path/to/storage"
    ... })
    >>> await provider.write("file.txt", b"Hello, World!")
    >>> data = await provider.read("file.txt")
    >>> print(data.decode())
"""

from pepperpy.storage.base import (
    StorageError,
    StorageObject,
    StorageProvider,
    StorageStats,
)
from pepperpy.storage.local import LocalStorageProvider

__all__ = [
    "StorageError",
    "StorageObject",
    "StorageProvider",
    "StorageStats",
    "LocalStorageProvider",
]
