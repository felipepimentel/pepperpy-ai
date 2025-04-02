"""Result caching module for PepperPy.

This module provides a caching system for storing operation results,
improving performance by avoiding redundant operations.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

import xxhash
from diskcache import Cache

from pepperpy.core.base import PepperpyError
from pepperpy.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ResultCacheError(PepperpyError):
    """Error raised by result cache operations."""

    pass


class ResultCache:
    """Cache for operation results.

    This class provides a versatile cache for storing operation results,
    with support for different cache backends, TTL, and metadata tagging.
    """

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        ttl: Optional[int] = None,
        backend: str = "disk",
        namespace: str = "default",
        max_size: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize result cache.

        Args:
            cache_dir: Directory to store cache files, defaults to .pepperpy/cache/results
            ttl: Default TTL (time to live) for cache entries in seconds, defaults to 1 day
            backend: Cache backend to use ('memory', 'disk')
            namespace: Cache namespace for segmenting cache
            max_size: Maximum size of cache in bytes (disk) or entries (memory)
            **kwargs: Additional configuration options
        """
        # Set cache directory
        if cache_dir is None:
            home_dir = Path.home()
            cache_dir = home_dir / ".pepperpy" / "cache" / "results" / namespace
        elif isinstance(cache_dir, str):
            cache_dir = Path(cache_dir)
            if namespace:
                cache_dir = cache_dir / namespace

        self.cache_dir = cache_dir
        self.namespace = namespace
        self.ttl = ttl or 24 * 60 * 60  # 1 day in seconds
        self.backend = backend
        self.max_size = max_size

        # Initialize backend
        if backend == "memory":
            self._cache: Dict[str, Dict[str, Any]] = {}
        elif backend == "disk":
            self._init_disk_cache()
        else:
            raise ValueError(f"Unsupported cache backend: {backend}")

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.start_time = time.time()

    def _init_disk_cache(self) -> None:
        """Initialize disk cache."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            disk_cache = Cache(directory=str(self.cache_dir))
            if self.max_size:
                disk_cache.reset(self.max_size)
            self._cache = disk_cache
        except Exception as e:
            logger.error(f"Failed to initialize disk cache: {e}")
            # Fallback to memory cache
            self._cache = {}
            self.backend = "memory"

    def _fast_hash(self, data: Union[str, bytes, Dict[str, Any]]) -> str:
        """Generate a fast hash from data.

        Args:
            data: Data to hash

        Returns:
            Hash string
        """
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            data = json.dumps(data, sort_keys=True)

        if isinstance(data, str):
            data = data.encode()

        return xxhash.xxh64(data).hexdigest()

    def _secure_hash(self, data: Union[str, bytes, Dict[str, Any]]) -> str:
        """Generate a secure hash from data.

        Args:
            data: Data to hash

        Returns:
            Hash string
        """
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            data = json.dumps(data, sort_keys=True)

        if isinstance(data, str):
            data = data.encode()

        return hashlib.sha256(data).hexdigest()

    def generate_key(
        self,
        params: Dict[str, Any],
        operation: str,
        fast: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a cache key for an operation.

        Args:
            params: Operation parameters
            operation: Operation name
            fast: Whether to use fast or secure hash
            context: Optional context variables that affect the result

        Returns:
            Cache key string
        """
        # Prepare data for hash
        data: Dict[str, Any] = {
            "op": operation,
            "params": params,
        }

        if context:
            # Only include relevant context keys
            filtered_context = {
                k: v
                for k, v in context.items()
                if k in ["model", "temperature", "language", "options"]
            }
            if filtered_context:
                data["context"] = filtered_context

        # Create hash
        if fast:
            return self._fast_hash(data)
        return self._secure_hash(data)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if self.backend == "memory":
            entry = self._cache.get(key)
            if not entry:
                self.misses += 1
                return None

            # Check expiry
            if "expiry" in entry and entry["expiry"] < time.time():
                # Expired
                self._cache.pop(key, None)
                self.misses += 1
                return None

            self.hits += 1
            return entry["value"]
        else:
            # Disk cache
            try:
                value = self._cache.get(key)
                if value is None:
                    self.misses += 1
                    return None
                self.hits += 1
                return value
            except Exception as e:
                logger.debug(f"Cache get error: {e}")
                self.misses += 1
                return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Custom TTL in seconds, overrides default
            metadata: Additional metadata to store with value

        Returns:
            True if cache entry was set successfully
        """
        expiry = time.time() + (ttl if ttl is not None else self.ttl)

        try:
            if self.backend == "memory":
                self._cache[key] = {
                    "value": value,
                    "expiry": expiry,
                    "metadata": metadata or {},
                    "timestamp": time.time(),
                }
                return True
            else:
                # Disk cache handles TTL internally
                # We know _cache is a diskcache.Cache instance here
                cache = cast(Cache, self._cache)
                cache.set(
                    key,
                    value,
                    expire=ttl if ttl is not None else self.ttl,
                    tag=metadata.get("tags", []) if metadata else None,
                )
                return True
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if cache entry was deleted successfully
        """
        try:
            if self.backend == "memory":
                if key in self._cache:
                    del self._cache[key]
                return True
            else:
                # We know _cache is a diskcache.Cache instance here
                cache = cast(Cache, self._cache)
                cache.delete(key)
                return True
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")
            return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        try:
            if self.backend == "memory":
                count = len(self._cache)
                self._cache.clear()
                return count
            else:
                # Get count first (approximate for disk cache)
                count = len(self._cache)
                self._cache.clear()
                return count
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        total_requests = self.hits + self.misses
        uptime = time.time() - self.start_time

        stats = {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": self.hits / total_requests if total_requests > 0 else 0,
            "requests_per_second": total_requests / uptime if uptime > 0 else 0,
            "backend": self.backend,
            "namespace": self.namespace,
            "ttl": self.ttl,
        }

        # Add backend-specific stats
        if self.backend == "memory":
            stats.update(
                {
                    "entries": len(self._cache),
                    "memory_usage_approx": "N/A",  # Would need to calculate
                }
            )
        else:
            # Disk cache stats
            try:
                # We know _cache is a diskcache.Cache instance here
                cache = cast(Cache, self._cache)
                stats.update(
                    {
                        "entries": len(cache),
                        "size_bytes": cache.volume(),
                        "directory": str(self.cache_dir),
                    }
                )
            except Exception:
                pass

        return stats


# Decorator for function caching
def cached(
    ttl: Optional[int] = None,
    namespace: Optional[str] = None,
    key_params: Optional[list[str]] = None,
) -> Callable:
    """Decorator for caching function results.

    Args:
        ttl: Cache TTL in seconds
        namespace: Cache namespace
        key_params: List of parameter names to include in cache key

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        # Get cache for this function
        cache_ns = namespace or f"{func.__module__}.{func.__name__}"
        cache = get_result_cache(namespace=cache_ns)

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name and arguments
            params = kwargs.copy()

            # Add positional args
            for i, arg in enumerate(args):
                params[f"arg{i}"] = arg

            # Filter key params if specified
            if key_params:
                params = {k: params[k] for k in key_params if k in params}

            key = cache.generate_key(params, func.__name__)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Not in cache, call function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(key, result, ttl=ttl)
            return result

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            params = kwargs.copy()

            # Add positional args
            for i, arg in enumerate(args):
                params[f"arg{i}"] = arg

            # Filter key params if specified
            if key_params:
                params = {k: params[k] for k in key_params if k in params}

            key = cache.generate_key(params, func.__name__)

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Not in cache, call function
            result = func(*args, **kwargs)

            # Cache result
            cache.set(key, result, ttl=ttl)
            return result

        # Return appropriate wrapper based on if function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global cache registry
_cache_registry: Dict[str, ResultCache] = {}


def get_result_cache(
    namespace: str = "default",
    cache_dir: Optional[Union[str, Path]] = None,
    ttl: Optional[int] = None,
    backend: str = "disk",
    **kwargs: Any,
) -> ResultCache:
    """Get or create a result cache instance.

    Args:
        namespace: Cache namespace
        cache_dir: Custom cache directory
        ttl: Default TTL in seconds
        backend: Cache backend ('memory' or 'disk')
        **kwargs: Additional configuration

    Returns:
        Result cache instance
    """
    cache_key = f"{namespace}:{backend}"

    if cache_key not in _cache_registry:
        _cache_registry[cache_key] = ResultCache(
            cache_dir=cache_dir,
            ttl=ttl,
            backend=backend,
            namespace=namespace,
            **kwargs,
        )

    return _cache_registry[cache_key]
