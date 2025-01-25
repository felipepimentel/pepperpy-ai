"""Cache module for Pepperpy framework.

This module provides caching implementations for different backends
and strategies.
"""

from pepperpy.persistence.cache.base import BaseCache, CacheError

__all__ = [
    "BaseCache",
    "CacheError",
]
