"""
PepperPy Cache Module.

This module provides caching capabilities for PepperPy.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.cache.base import CacheProvider

# Import the ResultCache and related functions
from pepperpy.cache.result_cache import (
    ResultCache,
    ResultCacheError,
    cached,
    get_result_cache,
    invalidate_cache,
)

__all__ = [
    "CacheProvider",
    "ResultCache",
    "ResultCacheError",
    "cached",
    "get_cache",
    "get_result_cache",
    "invalidate_cache",
]


def get_cache(
    namespace: str = "default",
    cache_dir: str | Path | None = None,
    ttl: int | None = None,
    backend: str = "disk",
    **kwargs: Any,
) -> ResultCache:
    """Get a cache instance with the specified configuration.

    This is a convenience function that calls get_result_cache.

    Args:
        namespace: Cache namespace for segmentation
        cache_dir: Custom cache directory
        ttl: Default TTL for cache entries in seconds
        backend: Cache backend ('memory' or 'disk')
        **kwargs: Additional configuration

    Returns:
        Configured cache instance
    """
    return get_result_cache(
        namespace=namespace, cache_dir=cache_dir, ttl=ttl, backend=backend, **kwargs
    )
