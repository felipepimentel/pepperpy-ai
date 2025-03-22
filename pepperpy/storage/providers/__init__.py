"""Storage provider implementations for PepperPy.

This module provides concrete implementations of storage providers,
supporting different storage backends and access patterns.

Example:
    >>> from pepperpy.storage.providers import LocalStorageProvider
    >>> storage = LocalStorageProvider(config={"root_dir": "/tmp/data"})
    >>> await storage.write("key", "value")
    >>> value = await storage.read("key")
"""

from pepperpy.storage.providers.local import LocalStorageProvider

__all__ = [
    "LocalStorageProvider",
]
