"""Result caching module for PepperPy.

This module provides a caching system for storing operation results,
improving performance by avoiding redundant operations.
"""

import fnmatch
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union, cast

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
        remote_uri: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize result cache.

        Args:
            cache_dir: Directory to store cache files, defaults to .pepperpy/cache/results
            ttl: Default TTL (time to live) for cache entries in seconds, defaults to 1 day
            backend: Cache backend to use ('memory', 'disk', 'redis')
            namespace: Cache namespace for segmenting cache
            max_size: Maximum size of cache in bytes (disk) or entries (memory)
            remote_uri: URI for remote cache (e.g., redis://localhost:6379/0)
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
        self.remote_uri = remote_uri

        # Key index for pattern-based operations
        self._key_index: Set[str] = set()

        # Initialize backend
        if backend == "memory":
            self._memory_cache: Dict[str, Dict[str, Any]] = {}
            self._disk_cache = None
            self._redis = None
        elif backend == "disk":
            self._memory_cache = None
            self._init_disk_cache()
        elif backend == "redis" and remote_uri:
            self._memory_cache = None
            self._disk_cache = None
            self._init_redis_cache()
        else:
            raise ValueError(f"Unsupported cache backend: {backend} or missing remote_uri")

        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.start_time = time.time()
        self.invalids = 0  # Counter for invalidations
        self.total_keys = 0  # Total keys ever stored

    def _init_disk_cache(self) -> None:
        """Initialize disk cache."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._disk_cache = Cache(directory=str(self.cache_dir))
            if self.max_size:
                self._disk_cache.reset(self.max_size)
            
            # Build key index from disk
            self._rebuild_key_index()
        except Exception as e:
            logger.error(f"Failed to initialize disk cache: {e}")
            # Fallback to memory cache
            self._memory_cache = {}
            self._disk_cache = None
            self.backend = "memory"
    
    def _init_redis_cache(self) -> None:
        """Initialize Redis cache."""
        try:
            # Lazy import to avoid dependency if not used
            import redis
            from redis import Redis
            
            if not self.remote_uri:
                raise ValueError("Remote URI is required for Redis backend")
            
            # Parse URI and create connection
            self._redis = Redis.from_url(str(self.remote_uri))
            # Test connection
            self._redis.ping()
            logger.info(f"Connected to Redis cache at {self.remote_uri}")
            
            # Set namespace prefix
            self._redis_prefix = f"pepperpy:{self.namespace}:"
            
        except ImportError:
            logger.error("Redis package not installed but redis backend requested")
            logger.info("Falling back to disk cache")
            self.backend = "disk"
            self._init_disk_cache()
        except (redis.RedisError, ValueError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Falling back to disk cache")
            self.backend = "disk"
            self._init_disk_cache()
    
    def _rebuild_key_index(self) -> None:
        """Rebuild key index from disk cache."""
        if self.backend == "disk" and self._disk_cache:
            try:
                self._key_index = set(self._disk_cache.iterkeys())
            except Exception as e:
                logger.error(f"Failed to rebuild key index: {e}")
                self._key_index = set()
        elif self.backend == "redis" and self._redis:
            try:
                # Get all keys with namespace prefix
                prefix = self._redis_prefix
                all_keys = self._redis.keys(f"{prefix}*")
                # Remove prefix from keys to get true keys
                self._key_index = {k.decode().replace(prefix, "") for k in all_keys}
            except Exception as e:
                logger.error(f"Failed to rebuild Redis key index: {e}")
                self._key_index = set()

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

    def get(self, key: str, detailed: bool = False) -> Union[Optional[Any], Dict[str, Any]]:
        """Get value from cache.

        Args:
            key: Cache key
            detailed: Whether to return detailed info including metadata

        Returns:
            Cached value or None if not found or expired
            If detailed=True, returns dict with 'value', 'metadata', 'ttl'
        """
        if self.backend == "memory" and self._memory_cache is not None:
            entry = self._memory_cache.get(key)
            if not entry:
                self.misses += 1
                return None if not detailed else {"value": None}

            # Check expiry
            if "expiry" in entry and entry["expiry"] < time.time():
                # Expired
                self._memory_cache.pop(key, None)
                self._key_index.discard(key)
                self.misses += 1
                return None if not detailed else {"value": None}

            self.hits += 1
            
            if detailed:
                ttl = entry.get("expiry", 0) - time.time()
                return {
                    "value": entry["value"],
                    "metadata": entry.get("metadata", {}),
                    "ttl": max(0, ttl),
                    "created": entry.get("created", 0)
                }
            return entry["value"]
        
        elif self.backend == "redis" and self._redis:
            try:
                redis_key = f"{self._redis_prefix}{key}"
                
                # Get value and metadata in a pipeline
                pipe = self._redis.pipeline()
                pipe.get(redis_key)
                pipe.hgetall(f"{redis_key}:meta")
                pipe.ttl(redis_key)
                
                value_bin, meta_dict, ttl = pipe.execute()
                
                if not value_bin:
                    self.misses += 1
                    self._key_index.discard(key)
                    return None if not detailed else {"value": None}
                
                # Decode value
                try:
                    value = json.loads(value_bin)
                except Exception:
                    # Raw string value
                    value = value_bin.decode()
                
                # Parse metadata
                metadata = {}
                created = 0
                if meta_dict:
                    try:
                        for k, v in meta_dict.items():
                            k_str = k.decode() if isinstance(k, bytes) else k
                            v_str = v.decode() if isinstance(v, bytes) else v
                            
                            if k_str == "created":
                                created = float(v_str)
                            elif k_str == "metadata":
                                metadata = json.loads(v_str)
                            else:
                                metadata[k_str] = v_str
                    except Exception as e:
                        logger.warning(f"Error parsing cache metadata: {e}")
                
                self.hits += 1
                
                if detailed:
                    return {
                        "value": value,
                        "metadata": metadata,
                        "ttl": max(0, ttl),
                        "created": created
                    }
                return value
                
            except Exception as e:
                logger.error(f"Redis cache error: {e}")
                self.misses += 1
                return None if not detailed else {"value": None}
        
        elif self.backend == "disk" and self._disk_cache:
            # Disk cache
            try:
                value = self._disk_cache.get(key)
                if value is None:
                    self.misses += 1
                    self._key_index.discard(key)
                    return None if not detailed else {"value": None}
                
                self.hits += 1
                
                # For detailed info, need to get metadata
                if detailed:
                    try:
                        # Try to get metadata
                        meta = self._disk_cache.get(f"{key}:meta", {})
                        ttl = self._disk_cache.expire(key, default=0)
                        created = meta.get("created", 0)
                        
                        return {
                            "value": value,
                            "metadata": meta.get("metadata", {}),
                            "ttl": max(0, ttl),
                            "created": created
                        }
                    except Exception:
                        # Fall back to simple value if metadata fetch fails
                        return {"value": value, "metadata": {}, "ttl": 0, "created": 0}
                
                return value
            except Exception as e:
                logger.error(f"Cache error: {e}")
                self.misses += 1
                return None if not detailed else {"value": None}
        else:
            # Something is wrong with the configuration
            self.misses += 1
            return None if not detailed else {"value": None}

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds, defaults to cache instance ttl
            metadata: Optional metadata to store with value
            tags: Optional tags for categorizing and finding cache entries

        Returns:
            True if successful, False otherwise
        """
        ttl_value = ttl if ttl is not None else self.ttl
        created = time.time()
        
        # Add to key index
        self._key_index.add(key)
        self.total_keys += 1
        
        meta_dict = {"created": created}
        if metadata:
            meta_dict["metadata"] = metadata
        if tags:
            meta_dict["tags"] = tags

        if self.backend == "memory" and self._memory_cache is not None:
            try:
                self._memory_cache[key] = {
                    "value": value,
                    "expiry": created + ttl_value,
                    "created": created,
                    "metadata": metadata or {},
                    "tags": tags or [],
                }
                return True
            except Exception as e:
                logger.error(f"Error setting cache: {e}")
                return False
        
        elif self.backend == "redis" and self._redis:
            try:
                redis_key = f"{self._redis_prefix}{key}"
                
                # Prepare value (serialize if needed)
                if isinstance(value, (dict, list, tuple, bool, int, float)) or value is None:
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                # Create a pipeline for atomic operations
                pipe = self._redis.pipeline()
                
                # Set value with TTL
                pipe.setex(redis_key, ttl_value, value_str)
                
                # Set metadata as hash
                if metadata or tags:
                    meta_key = f"{redis_key}:meta"
                    pipe.delete(meta_key)  # Clear existing metadata
                    
                    if metadata:
                        pipe.hset(meta_key, "metadata", json.dumps(metadata))
                    
                    if tags:
                        pipe.hset(meta_key, "tags", json.dumps(tags))
                    
                    pipe.hset(meta_key, "created", str(created))
                    pipe.expire(meta_key, ttl_value)
                
                pipe.execute()
                return True
                
            except Exception as e:
                logger.error(f"Redis cache error: {e}")
                return False
        
        elif self.backend == "disk" and self._disk_cache:
            # Disk cache
            try:
                # Store value with TTL
                success = self._disk_cache.set(key, value, ttl_value)
                
                # Store metadata separately
                if metadata or tags:
                    meta_data = {
                        "created": created,
                        "metadata": metadata or {},
                    }
                    if tags:
                        meta_data["tags"] = tags
                    
                    self._disk_cache.set(f"{key}:meta", meta_data, ttl_value)
                
                return success
            except Exception as e:
                logger.error(f"Cache error: {e}")
                return False
        else:
            # Invalid configuration
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        self._key_index.discard(key)
        
        if self.backend == "memory" and self._memory_cache is not None:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False
        
        elif self.backend == "redis" and self._redis:
            try:
                redis_key = f"{self._redis_prefix}{key}"
                
                # Delete both value and metadata
                pipe = self._redis.pipeline()
                pipe.delete(redis_key)
                pipe.delete(f"{redis_key}:meta")
                
                results = pipe.execute()
                return any(count > 0 for count in results)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                return False
        
        elif self.backend == "disk" and self._disk_cache:
            # Disk cache
            try:
                # Delete value and metadata
                success = self._disk_cache.delete(key)
                self._disk_cache.delete(f"{key}:meta")
                return success
            except Exception as e:
                logger.error(f"Cache delete error: {e}")
                return False
        else:
            # Invalid configuration
            return False

    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries by key pattern.

        Args:
            pattern: Glob pattern to match keys (e.g., "user_*", "query_*_analytics")

        Returns:
            Number of invalidated entries
        """
        if not pattern:
            return 0
            
        count = 0
        
        # Use the key index to efficiently find matching keys
        matching_keys = [k for k in self._key_index if fnmatch.fnmatch(k, pattern)]
        
        # Delete all matching keys
        for key in matching_keys:
            if self.delete(key):
                count += 1
        
        if count > 0:
            logger.info(f"Invalidated {count} cache entries with pattern '{pattern}'")
            self.invalids += count
        
        return count
    
    def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate cache entries by tag.

        Args:
            tag: Tag to match

        Returns:
            Number of invalidated entries
        """
        if not tag:
            return 0
            
        count = 0
        
        if self.backend == "memory" and self._memory_cache is not None:
            # Identify keys with matching tag
            matching_keys = []
            for key, entry in self._memory_cache.items():
                tags = entry.get("tags", [])
                if tag in tags:
                    matching_keys.append(key)
            
            # Delete all matching keys
            for key in matching_keys:
                if self.delete(key):
                    count += 1
        
        elif self.backend == "redis" and self._redis:
            # We need to scan all keys and check their tags
            try:
                # Get all keys with our prefix
                all_keys = self._redis.keys(f"{self._redis_prefix}*:meta")
                
                # Find keys with matching tag
                matching_keys = []
                for meta_key in all_keys:
                    try:
                        tags_json = self._redis.hget(meta_key, "tags")
                        if not tags_json:
                            continue
                            
                        tags = json.loads(tags_json)
                        if tag in tags:
                            # Extract original key from meta key
                            original_key = meta_key.decode().replace(f"{self._redis_prefix}", "").replace(":meta", "")
                            matching_keys.append(original_key)
                    except Exception:
                        continue
                
                # Delete all matching keys
                for key in matching_keys:
                    if self.delete(key):
                        count += 1
                        
            except Exception as e:
                logger.error(f"Redis tag invalidation error: {e}")
        
        elif self.backend == "disk" and self._disk_cache:
            # For disk cache, we need to scan keys and check their metadata
            try:
                matching_keys = []
                
                # Scan all keys with :meta suffix
                for key in self._disk_cache.iterkeys():
                    if not key.endswith(":meta"):
                        continue
                    
                    # Get metadata and check tags
                    meta = self._disk_cache.get(key)
                    if not meta or not isinstance(meta, dict):
                        continue
                        
                    tags = meta.get("tags", [])
                    if tag in tags:
                        # Extract original key
                        original_key = key[:-5]  # Remove :meta suffix
                        matching_keys.append(original_key)
                
                # Delete all matching keys
                for key in matching_keys:
                    if self.delete(key):
                        count += 1
                        
            except Exception as e:
                logger.error(f"Disk cache tag invalidation error: {e}")
        
        if count > 0:
            logger.info(f"Invalidated {count} cache entries with tag '{tag}'")
            self.invalids += count
        
        return count

    def clear(self) -> int:
        """Clear the entire cache.

        Returns:
            Number of entries cleared
        """
        try:
            if self.backend == "memory" and self._memory_cache is not None:
                count = len(self._memory_cache)
                self._memory_cache.clear()
                self._key_index.clear()
                
            elif self.backend == "redis" and self._redis:
                # Delete all keys with our prefix
                try:
                    keys = self._redis.keys(f"{self._redis_prefix}*")
                    count = len(keys)
                    if keys:
                        self._redis.delete(*keys)
                    self._key_index.clear()
                except Exception as e:
                    logger.error(f"Redis clear error: {e}")
                    count = 0
                    
            elif self.backend == "disk" and self._disk_cache:
                # Disk cache
                count = len(list(self._disk_cache.iterkeys()))
                self._disk_cache.clear()
                self._key_index.clear()
            else:
                # Invalid configuration
                count = 0
                
            self.invalids += count
            return count
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of statistics
        """
        uptime = time.time() - self.start_time
        total_ops = self.hits + self.misses
        
        stats = {
            "backend": self.backend,
            "namespace": self.namespace,
            "uptime": uptime,
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalids,
            "total_keys_stored": self.total_keys,
            "hit_rate": self.hits / total_ops if total_ops > 0 else 0,
            "active_entries": 0,
        }
        
        # Get count of active entries
        try:
            if self.backend == "memory" and self._memory_cache is not None:
                stats["active_entries"] = len(self._memory_cache)
                stats["memory_usage"] = sum(
                    len(json.dumps(v)) for v in self._memory_cache.values()
                )
                stats["storage_path"] = "memory"
                
            elif self.backend == "redis" and self._redis:
                # Count keys with our prefix
                try:
                    keys = self._redis.keys(f"{self._redis_prefix}*")
                    stats["active_entries"] = len(keys) // 2  # Divide by 2 because we store value and metadata separately
                    stats["storage_path"] = self.remote_uri
                    stats["memory_usage"] = None  # Can't easily determine for Redis
                except Exception as e:
                    logger.error(f"Redis stats error: {e}")
                    
            elif self.backend == "disk" and self._disk_cache:
                # Disk cache
                stats["active_entries"] = len(list(self._disk_cache.iterkeys()))
                stats["storage_path"] = str(self.cache_dir)
                
                # Get disk usage if available
                try:
                    import shutil
                    stats["memory_usage"] = shutil.disk_usage(str(self.cache_dir)).used
                except Exception:
                    stats["memory_usage"] = None
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
        
        return stats


def cached(
    ttl: Optional[int] = None,
    namespace: Optional[str] = None,
    key_params: Optional[list[str]] = None,
    tags: Optional[List[str]] = None,
    backend: Optional[str] = None,
) -> Callable:
    """Decorator for caching function results.

    Args:
        ttl: TTL for cache entries in seconds, defaults to 1 hour
        namespace: Cache namespace, defaults to function name
        key_params: List of parameter names to include in cache key
        tags: Tags to add to cache entries for categorization
        backend: Specific backend to use, overrides system default

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        # Get cache for this function
        cache_ns = namespace or func.__qualname__
        func_cache = get_result_cache(namespace=cache_ns, backend=backend)

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name and arguments
            params: Dict[str, Any] = {}
            
            # Add positional arguments to params
            if args:
                params["args"] = [
                    str(arg) if isinstance(arg, (bytes, Path)) else arg for arg in args
                ]
                
            # Add keyword arguments
            if key_params:
                # Only include specified parameters
                for param in key_params:
                    if param in kwargs:
                        params[param] = kwargs[param]
            else:
                # Include all parameters except those starting with _
                params.update({
                    k: v for k, v in kwargs.items() if not k.startswith("_")
                })
                
            # Generate key
            cache_key = func_cache.generate_key(params, func.__qualname__)
            
            # Check cache
            cached_result = func_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call function if not in cache
            result = await func(*args, **kwargs)
            
            # Cache result
            func_cache.set(cache_key, result, ttl=ttl, tags=tags)
            
            return result

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            params: Dict[str, Any] = {}
            
            # Add positional arguments to params
            if args:
                params["args"] = [
                    str(arg) if isinstance(arg, (bytes, Path)) else arg for arg in args
                ]
                
            # Add keyword arguments
            if key_params:
                # Only include specified parameters
                for param in key_params:
                    if param in kwargs:
                        params[param] = kwargs[param]
            else:
                # Include all parameters except those starting with _
                params.update({
                    k: v for k, v in kwargs.items() if not k.startswith("_")
                })
                
            # Generate key
            cache_key = func_cache.generate_key(params, func.__qualname__)
            
            # Check cache
            cached_result = func_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Call function if not in cache
            result = func(*args, **kwargs)
            
            # Cache result
            func_cache.set(cache_key, result, ttl=ttl, tags=tags)
            
            return result

        # Use the appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
                
        return sync_wrapper

    return decorator


def get_result_cache(
    namespace: str = "default",
    cache_dir: Optional[Union[str, Path]] = None,
    ttl: Optional[int] = None,
    backend: Optional[str] = None,
    remote_uri: Optional[str] = None,
    **kwargs: Any,
) -> ResultCache:
    """Get a result cache instance.

    This function allows getting a shared cache instance for a namespace.

    Args:
        namespace: Cache namespace
        cache_dir: Cache directory
        ttl: Default TTL
        backend: Cache backend ('memory', 'disk', 'redis')
        remote_uri: URI for remote cache
        **kwargs: Additional cache configuration

    Returns:
        ResultCache instance
    """
    # Get system default backend if not specified
    if backend is None:
        import os
        backend = os.environ.get("PEPPERPY_CACHE_BACKEND", "disk")
        
    # Get system default remote URI if not specified and using Redis backend
    if backend == "redis" and remote_uri is None:
        import os
        remote_uri = os.environ.get("PEPPERPY_REDIS_URI", "redis://localhost:6379/0")

    # Create cache instance
    cache = ResultCache(
        cache_dir=cache_dir,
        ttl=ttl,
        backend=backend,
        namespace=namespace,
        remote_uri=remote_uri,
        **kwargs,
    )

    return cache


def invalidate_cache(
    namespace: Optional[str] = None,
    pattern: Optional[str] = None,
    tag: Optional[str] = None,
    backend: Optional[str] = None,
) -> int:
    """Invalidate cache entries.

    This function invalidates cache entries based on namespace, pattern, or tag.

    Args:
        namespace: Cache namespace to invalidate
        pattern: Key pattern to invalidate
        tag: Tag to invalidate
        backend: Specific backend to use

    Returns:
        Number of invalidated entries
    """
    # Get cache for specified namespace
    cache = get_result_cache(namespace=namespace or "default", backend=backend)
    
    # Count invalidated entries
    count = 0
    
    # Clear entire namespace if no pattern or tag
    if not pattern and not tag:
        return cache.clear()
        
    # Invalidate by pattern
    if pattern:
        count += cache.invalidate_by_pattern(pattern)
        
    # Invalidate by tag
    if tag:
        count += cache.invalidate_by_tag(tag)
        
    return count
