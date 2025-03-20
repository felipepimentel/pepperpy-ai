"""Storage provider implementations for PepperPy.

This module provides concrete implementations of storage providers,
supporting different storage backends and access patterns.

Example:
    >>> from pepperpy.storage.providers import LocalStorage
    >>> storage = LocalStorage(path="/tmp/data")
    >>> await storage.save("key", "value")
    >>> value = await storage.load("key")
"""

from pepperpy.storage.providers.local import LocalStorage
from pepperpy.storage.providers.db import DatabaseStorage
from pepperpy.storage.providers.rest import RESTStorage
from pepperpy.storage.providers.object_store import ObjectStorage

__all__ = [
    "LocalStorage",
    "DatabaseStorage",
    "RESTStorage",
    "ObjectStorage",
] 