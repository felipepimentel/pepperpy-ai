"""Caching capabilities for PepperPy.

This module provides interfaces and implementations for working with
caching systems, including in-memory and persistent storage.

Example:
    >>> from pepperpy.cache import CacheProvider
    >>> provider = CacheProvider.from_config({
    ...     "provider": "memory",
    ...     "max_size": 1000
    ... })
    >>> await provider.set("key", "value", ttl=60)
    >>> value = await provider.get("key")
    >>> print(value)
"""

from pepperpy.cache.base import CacheProvider
from pepperpy.cache.memory import MemoryCacheProvider

__all__ = [
    "CacheProvider",
    "MemoryCacheProvider",
]
