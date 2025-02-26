"""Unified caching system for Pepperpy.

This module provides a centralized caching solution with configurable policies,
metrics collection, and support for different storage backends.
"""

from pepperpy.caching.base import CacheBackend
from pepperpy.caching.invalidation.strategy import InvalidationStrategy
from pepperpy.caching.metrics.collector import CacheMetrics
from pepperpy.caching.policies.base import CachePolicy
from pepperpy.caching.stores.base import CacheStore

__all__ = [
    "CacheBackend",
    "CacheMetrics",
    "CachePolicy",
    "CacheStore",
    "InvalidationStrategy",
]
