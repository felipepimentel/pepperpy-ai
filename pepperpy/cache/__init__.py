"""Cache module for PepperPy.

This module provides caching functionality for improving performance
by storing and reusing operation results.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.cache.result_cache import (
    ResultCache,
    ResultCacheError,
    cached,
    get_result_cache,
    invalidate_cache,
)

__all__ = [
    "ResultCache",
    "ResultCacheError",
    "cached",
    "get_result_cache",
    "get_cache",
    "invalidate_cache",
]


def get_cache(
    namespace: str = "default",
    cache_dir: Optional[Union[str, Path]] = None,
    ttl: Optional[int] = None,
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
