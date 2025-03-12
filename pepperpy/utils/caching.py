"""Advanced caching strategies for PepperPy.

This module provides advanced caching strategies with TTL and invalidation
mechanisms for the PepperPy framework.
"""

import functools
import hashlib
import inspect
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar, cast

from pepperpy.cache import (
    AsyncCacheManager,
    CacheManager,
    get_async_cache_manager,
    get_cache_manager,
)
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


class InvalidationStrategy(Enum):
    """Invalidation strategy for cache entries.

    This enum defines different strategies for invalidating cache entries.
    """

    # Invalidate cache entries when they expire (TTL)
    TTL = "ttl"
    # Invalidate cache entries when they are accessed (LRU)
    LRU = "lru"
    # Invalidate cache entries based on a pattern
    PATTERN = "pattern"
    # Invalidate cache entries based on dependencies
    DEPENDENCY = "dependency"
    # Invalidate cache entries based on a version
    VERSION = "version"
    # Invalidate cache entries manually
    MANUAL = "manual"


@dataclass
class CacheInvalidationRule:
    """Cache invalidation rule.

    A cache invalidation rule defines when and how cache entries should be
    invalidated.
    """

    # The invalidation strategy to use
    strategy: InvalidationStrategy
    # The pattern to match for pattern-based invalidation
    pattern: Optional[str] = None
    # The dependencies for dependency-based invalidation
    dependencies: List[str] = field(default_factory=list)
    # The version for version-based invalidation
    version: Optional[str] = None
    # The TTL in seconds for TTL-based invalidation
    ttl: Optional[int] = None
    # The maximum size for LRU-based invalidation
    max_size: Optional[int] = None


class CacheInvalidator(Generic[T]):
    """Cache invalidator.

    A cache invalidator is responsible for invalidating cache entries based on
    different strategies.
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        namespace: str = "default",
    ):
        """Initialize a cache invalidator.

        Args:
            cache_manager: The cache manager to use, or None to use the global one
            namespace: The namespace to use for cache keys
        """
        self.cache_manager = cache_manager or get_cache_manager()
        self.namespace = namespace
        self.rules: Dict[str, CacheInvalidationRule] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.access_times: Dict[str, float] = {}
        self.versions: Dict[str, str] = {}
        self.size_limits: Dict[str, int] = {}
        self.current_sizes: Dict[str, int] = {}

    def add_rule(self, key_pattern: str, rule: CacheInvalidationRule) -> None:
        """Add an invalidation rule.

        Args:
            key_pattern: The pattern to match cache keys against
            rule: The invalidation rule to apply
        """
        self.rules[key_pattern] = rule

        # Set up dependencies
        if rule.strategy == InvalidationStrategy.DEPENDENCY:
            for dependency in rule.dependencies:
                if dependency not in self.dependencies:
                    self.dependencies[dependency] = set()
                self.dependencies[dependency].add(key_pattern)

        # Set up versions
        if rule.strategy == InvalidationStrategy.VERSION:
            if rule.version is not None:
                self.versions[key_pattern] = rule.version

        # Set up size limits
        if rule.strategy == InvalidationStrategy.LRU:
            if rule.max_size is not None:
                self.size_limits[key_pattern] = rule.max_size
                self.current_sizes[key_pattern] = 0

    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: The key to invalidate
        """
        # Delete the cache entry
        self.cache_manager.delete(key)

        # Update dependencies
        if key in self.dependencies:
            for dependent_key in self.dependencies[key]:
                self.invalidate(dependent_key)

    def invalidate_by_pattern(self, pattern: str) -> None:
        """Invalidate cache entries by pattern.

        Args:
            pattern: The pattern to match cache keys against
        """
        # This is a simplified implementation that would need to be adapted
        # to the actual cache backend's capabilities
        # In a real implementation, you might use the cache backend's
        # pattern matching capabilities, if available
        pass

    def invalidate_by_dependency(self, dependency: str) -> None:
        """Invalidate cache entries by dependency.

        Args:
            dependency: The dependency to invalidate
        """
        if dependency in self.dependencies:
            for key in self.dependencies[dependency]:
                self.invalidate(key)

    def invalidate_by_version(self, key_pattern: str, new_version: str) -> None:
        """Invalidate cache entries by version.

        Args:
            key_pattern: The pattern to match cache keys against
            new_version: The new version
        """
        if key_pattern in self.versions:
            old_version = self.versions[key_pattern]
            if old_version != new_version:
                self.versions[key_pattern] = new_version
                self.invalidate_by_pattern(key_pattern)

    def record_access(self, key: str) -> None:
        """Record an access to a cache entry.

        Args:
            key: The key that was accessed
        """
        self.access_times[key] = time.time()

    def check_lru(self, key_pattern: str) -> None:
        """Check if LRU eviction is needed.

        Args:
            key_pattern: The pattern to check
        """
        if key_pattern in self.size_limits and key_pattern in self.current_sizes:
            max_size = self.size_limits[key_pattern]
            current_size = self.current_sizes[key_pattern]

            if current_size > max_size:
                # Find the least recently used entries
                entries = sorted(
                    [
                        (k, v)
                        for k, v in self.access_times.items()
                        if k.startswith(key_pattern)
                    ],
                    key=lambda x: x[1],
                )

                # Evict entries until we're under the limit
                for key, _ in entries[: current_size - max_size]:
                    self.invalidate(key)
                    self.current_sizes[key_pattern] -= 1


class AsyncCacheInvalidator(Generic[T]):
    """Asynchronous cache invalidator.

    An asynchronous cache invalidator is responsible for invalidating cache
    entries based on different strategies.
    """

    def __init__(
        self,
        cache_manager: Optional[AsyncCacheManager] = None,
        namespace: str = "default",
    ):
        """Initialize an asynchronous cache invalidator.

        Args:
            cache_manager: The cache manager to use, or None to use the global one
            namespace: The namespace to use for cache keys
        """
        self.cache_manager = cache_manager or get_async_cache_manager()
        self.namespace = namespace
        self.rules: Dict[str, CacheInvalidationRule] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.access_times: Dict[str, float] = {}
        self.versions: Dict[str, str] = {}
        self.size_limits: Dict[str, int] = {}
        self.current_sizes: Dict[str, int] = {}

    def add_rule(self, key_pattern: str, rule: CacheInvalidationRule) -> None:
        """Add an invalidation rule.

        Args:
            key_pattern: The pattern to match cache keys against
            rule: The invalidation rule to apply
        """
        self.rules[key_pattern] = rule

        # Set up dependencies
        if rule.strategy == InvalidationStrategy.DEPENDENCY:
            for dependency in rule.dependencies:
                if dependency not in self.dependencies:
                    self.dependencies[dependency] = set()
                self.dependencies[dependency].add(key_pattern)

        # Set up versions
        if rule.strategy == InvalidationStrategy.VERSION:
            if rule.version is not None:
                self.versions[key_pattern] = rule.version

        # Set up size limits
        if rule.strategy == InvalidationStrategy.LRU:
            if rule.max_size is not None:
                self.size_limits[key_pattern] = rule.max_size
                self.current_sizes[key_pattern] = 0

    async def invalidate(self, key: str) -> None:
        """Invalidate a cache entry asynchronously.

        Args:
            key: The key to invalidate
        """
        # Delete the cache entry
        await self.cache_manager.adelete(key)

        # Update dependencies
        if key in self.dependencies:
            for dependent_key in self.dependencies[key]:
                await self.invalidate(dependent_key)

    async def invalidate_by_pattern(self, pattern: str) -> None:
        """Invalidate cache entries by pattern asynchronously.

        Args:
            pattern: The pattern to match cache keys against
        """
        # This is a simplified implementation that would need to be adapted
        # to the actual cache backend's capabilities
        # In a real implementation, you might use the cache backend's
        # pattern matching capabilities, if available
        pass

    async def invalidate_by_dependency(self, dependency: str) -> None:
        """Invalidate cache entries by dependency asynchronously.

        Args:
            dependency: The dependency to invalidate
        """
        if dependency in self.dependencies:
            for key in self.dependencies[dependency]:
                await self.invalidate(key)

    async def invalidate_by_version(self, key_pattern: str, new_version: str) -> None:
        """Invalidate cache entries by version asynchronously.

        Args:
            key_pattern: The pattern to match cache keys against
            new_version: The new version
        """
        if key_pattern in self.versions:
            old_version = self.versions[key_pattern]
            if old_version != new_version:
                self.versions[key_pattern] = new_version
                await self.invalidate_by_pattern(key_pattern)

    def record_access(self, key: str) -> None:
        """Record an access to a cache entry.

        Args:
            key: The key that was accessed
        """
        self.access_times[key] = time.time()

    async def check_lru(self, key_pattern: str) -> None:
        """Check if LRU eviction is needed asynchronously.

        Args:
            key_pattern: The pattern to check
        """
        if key_pattern in self.size_limits and key_pattern in self.current_sizes:
            max_size = self.size_limits[key_pattern]
            current_size = self.current_sizes[key_pattern]

            if current_size > max_size:
                # Find the least recently used entries
                entries = sorted(
                    [
                        (k, v)
                        for k, v in self.access_times.items()
                        if k.startswith(key_pattern)
                    ],
                    key=lambda x: x[1],
                )

                # Evict entries until we're under the limit
                for key, _ in entries[: current_size - max_size]:
                    await self.invalidate(key)
                    self.current_sizes[key_pattern] -= 1


class CachePolicy(ABC):
    """Cache policy.

    A cache policy defines how cache entries should be managed, including
    TTL, invalidation, and eviction.
    """

    @abstractmethod
    def should_cache(self, key: str, value: Any) -> bool:
        """Check if a value should be cached.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            True if the value should be cached, False otherwise
        """
        pass

    @abstractmethod
    def get_ttl(self, key: str, value: Any) -> Optional[int]:
        """Get the TTL for a cache entry.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            The TTL in seconds, or None for no expiration
        """
        pass

    @abstractmethod
    def should_invalidate(self, key: str, value: Any) -> bool:
        """Check if a cache entry should be invalidated.

        Args:
            key: The key of the cache entry
            value: The cached value

        Returns:
            True if the cache entry should be invalidated, False otherwise
        """
        pass


class DefaultCachePolicy(CachePolicy):
    """Default cache policy.

    This policy caches all values with a fixed TTL.
    """

    def __init__(self, ttl: Optional[int] = None):
        """Initialize a default cache policy.

        Args:
            ttl: The TTL in seconds, or None for no expiration
        """
        self.ttl = ttl

    def should_cache(self, key: str, value: Any) -> bool:
        """Check if a value should be cached.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            True if the value should be cached, False otherwise
        """
        return True

    def get_ttl(self, key: str, value: Any) -> Optional[int]:
        """Get the TTL for a cache entry.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            The TTL in seconds, or None for no expiration
        """
        return self.ttl

    def should_invalidate(self, key: str, value: Any) -> bool:
        """Check if a cache entry should be invalidated.

        Args:
            key: The key of the cache entry
            value: The cached value

        Returns:
            True if the cache entry should be invalidated, False otherwise
        """
        return False


class SizeLimitedCachePolicy(CachePolicy):
    """Size-limited cache policy.

    This policy caches values up to a maximum size.
    """

    def __init__(
        self,
        max_size: int,
        ttl: Optional[int] = None,
        size_func: Optional[Callable[[Any], int]] = None,
    ):
        """Initialize a size-limited cache policy.

        Args:
            max_size: The maximum size of the cache
            ttl: The TTL in seconds, or None for no expiration
            size_func: A function to calculate the size of a value, or None to use len()
        """
        self.max_size = max_size
        self.ttl = ttl
        self.size_func = size_func or (lambda x: len(str(x)))
        self.current_size = 0

    def should_cache(self, key: str, value: Any) -> bool:
        """Check if a value should be cached.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            True if the value should be cached, False otherwise
        """
        value_size = self.size_func(value)
        return self.current_size + value_size <= self.max_size

    def get_ttl(self, key: str, value: Any) -> Optional[int]:
        """Get the TTL for a cache entry.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            The TTL in seconds, or None for no expiration
        """
        return self.ttl

    def should_invalidate(self, key: str, value: Any) -> bool:
        """Check if a cache entry should be invalidated.

        Args:
            key: The key of the cache entry
            value: The cached value

        Returns:
            True if the cache entry should be invalidated, False otherwise
        """
        return False

    def add_value(self, value: Any) -> None:
        """Add a value to the cache size counter.

        Args:
            value: The value to add
        """
        self.current_size += self.size_func(value)

    def remove_value(self, value: Any) -> None:
        """Remove a value from the cache size counter.

        Args:
            value: The value to remove
        """
        self.current_size -= self.size_func(value)


class DynamicTTLCachePolicy(CachePolicy):
    """Dynamic TTL cache policy.

    This policy uses a function to determine the TTL for each cache entry.
    """

    def __init__(self, ttl_func: Callable[[str, Any], Optional[int]]):
        """Initialize a dynamic TTL cache policy.

        Args:
            ttl_func: A function to calculate the TTL for a cache entry
        """
        self.ttl_func = ttl_func

    def should_cache(self, key: str, value: Any) -> bool:
        """Check if a value should be cached.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            True if the value should be cached, False otherwise
        """
        return True

    def get_ttl(self, key: str, value: Any) -> Optional[int]:
        """Get the TTL for a cache entry.

        Args:
            key: The key to cache the value under
            value: The value to cache

        Returns:
            The TTL in seconds, or None for no expiration
        """
        return self.ttl_func(key, value)

    def should_invalidate(self, key: str, value: Any) -> bool:
        """Check if a cache entry should be invalidated.

        Args:
            key: The key of the cache entry
            value: The cached value

        Returns:
            True if the cache entry should be invalidated, False otherwise
        """
        return False


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    cache_manager: Optional[CacheManager] = None,
    policy: Optional[CachePolicy] = None,
    invalidator: Optional[CacheInvalidator] = None,
) -> Callable[[F], F]:
    """Decorator for caching function results.

    Args:
        ttl: The time-to-live in seconds, or None for no expiration
        key_prefix: A prefix for the cache key
        cache_manager: The cache manager to use, or None to use the global one
        policy: The cache policy to use, or None to use a default policy
        invalidator: The cache invalidator to use, or None to use a default invalidator

    Returns:
        A decorator for caching function results
    """

    def decorator(func: F) -> F:
        """Decorator for caching function results.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Get the cache manager
        cm = cache_manager or get_cache_manager()

        # Get the cache policy
        cp = policy or DefaultCachePolicy(ttl)

        # Get the function signature
        sig = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for caching function results.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The function result, possibly from cache
            """
            # Bind the arguments to the function signature
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Create a cache key
            key_parts = [key_prefix, func.__module__, func.__name__]
            for name, value in bound_args.arguments.items():
                key_parts.append(f"{name}={_hash_arg(value)}")

            key = ":".join(key_parts)

            # Check if the value is in the cache
            cached_value = cm.get(key)
            if cached_value is not None:
                # Record the access
                if invalidator is not None:
                    invalidator.record_access(key)

                return cached_value

            # Call the function
            result = func(*args, **kwargs)

            # Check if the result should be cached
            if cp.should_cache(key, result):
                # Get the TTL
                entry_ttl = cp.get_ttl(key, result)

                # Set the value in the cache
                cm.set(key, result, entry_ttl)

                # Update the cache size
                if isinstance(cp, SizeLimitedCachePolicy):
                    cp.add_value(result)

                # Record the access
                if invalidator is not None:
                    invalidator.record_access(key)

                    # Check if LRU eviction is needed
                    for pattern in invalidator.rules:
                        if (
                            invalidator.rules[pattern].strategy
                            == InvalidationStrategy.LRU
                        ):
                            invalidator.check_lru(pattern)

            return result

        return cast(F, wrapper)

    return decorator


def async_cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    cache_manager: Optional[AsyncCacheManager] = None,
    policy: Optional[CachePolicy] = None,
    invalidator: Optional[AsyncCacheInvalidator] = None,
) -> Callable[[F], F]:
    """Decorator for caching asynchronous function results.

    Args:
        ttl: The time-to-live in seconds, or None for no expiration
        key_prefix: A prefix for the cache key
        cache_manager: The cache manager to use, or None to use the global one
        policy: The cache policy to use, or None to use a default policy
        invalidator: The cache invalidator to use, or None to use a default invalidator

    Returns:
        A decorator for caching asynchronous function results
    """

    def decorator(func: F) -> F:
        """Decorator for caching asynchronous function results.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Get the cache manager
        cm = cache_manager or get_async_cache_manager()

        # Get the cache policy
        cp = policy or DefaultCachePolicy(ttl)

        # Get the function signature
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper for caching asynchronous function results.

            Args:
                *args: Positional arguments
                **kwargs: Keyword arguments

            Returns:
                The function result, possibly from cache
            """
            # Bind the arguments to the function signature
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Create a cache key
            key_parts = [key_prefix, func.__module__, func.__name__]
            for name, value in bound_args.arguments.items():
                key_parts.append(f"{name}={_hash_arg(value)}")

            key = ":".join(key_parts)

            # Check if the value is in the cache
            cached_value = await cm.aget(key)
            if cached_value is not None:
                # Record the access
                if invalidator is not None:
                    invalidator.record_access(key)

                return cached_value

            # Call the function
            result = await func(*args, **kwargs)

            # Check if the result should be cached
            if cp.should_cache(key, result):
                # Get the TTL
                entry_ttl = cp.get_ttl(key, result)

                # Set the value in the cache
                await cm.aset(key, result, entry_ttl)

                # Update the cache size
                if isinstance(cp, SizeLimitedCachePolicy):
                    cp.add_value(result)

                # Record the access
                if invalidator is not None:
                    invalidator.record_access(key)

                    # Check if LRU eviction is needed
                    for pattern in invalidator.rules:
                        if (
                            invalidator.rules[pattern].strategy
                            == InvalidationStrategy.LRU
                        ):
                            await invalidator.check_lru(pattern)

            return result

        return cast(F, wrapper)

    return decorator


def _hash_arg(arg: Any) -> str:
    """Hash an argument for use in a cache key.

    Args:
        arg: The argument to hash

    Returns:
        A hash of the argument
    """
    if isinstance(arg, (str, int, float, bool, type(None))):
        return str(arg)
    elif isinstance(arg, (list, tuple, set)):
        return f"[{','.join(_hash_arg(x) for x in arg)}]"
    elif isinstance(arg, dict):
        return (
            f"{{{','.join(f'{_hash_arg(k)}:{_hash_arg(v)}' for k, v in arg.items())}}}"
        )
    else:
        # For other types, use the hash of the string representation
        try:
            return hashlib.md5(str(arg).encode()).hexdigest()
        except:
            return hashlib.md5(str(id(arg)).encode()).hexdigest()


# Global cache invalidators
_cache_invalidator = CacheInvalidator()
_async_cache_invalidator = AsyncCacheInvalidator()


def get_cache_invalidator() -> CacheInvalidator:
    """Get the global cache invalidator.

    Returns:
        The global cache invalidator
    """
    return _cache_invalidator


def get_async_cache_invalidator() -> AsyncCacheInvalidator:
    """Get the global asynchronous cache invalidator.

    Returns:
        The global asynchronous cache invalidator
    """
    return _async_cache_invalidator
