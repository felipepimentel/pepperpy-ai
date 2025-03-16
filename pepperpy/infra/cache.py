"""Advanced caching strategies for PepperPy.

This module provides advanced caching strategies with TTL and invalidation
mechanisms for the PepperPy framework.

Typical usage:
    from pepperpy.infra.cache import cached, async_cached

    # Use the cached decorator for synchronous functions
    @cached(ttl=60)
    def get_user(user_id: str) -> dict:
        # Expensive operation to get user data
        return {"id": user_id, "name": "John Doe"}

    # Use the async_cached decorator for asynchronous functions
    @async_cached(ttl=60)
    async def get_user_async(user_id: str) -> dict:
        # Expensive operation to get user data
        return {"id": user_id, "name": "John Doe"}
"""

import asyncio
import functools
import hashlib
import inspect
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
    cast,
)

from pepperpy.cache import (
    AsyncCacheManager,
    CacheManager,
    get_async_cache_manager,
    get_cache_manager,
)
from pepperpy.infra.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variables
T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


class InvalidationStrategy(Enum):
    """Invalidation strategy for cache entries.

    This enum defines different strategies for invalidating cache entries.

    Args:
        TTL: Invalidate cache entries when they expire (TTL)
        LRU: Invalidate cache entries when they are accessed (LRU)
        PATTERN: Invalidate cache entries based on a pattern
        DEPENDENCY: Invalidate cache entries based on dependencies
        VERSION: Invalidate cache entries based on a version
        MANUAL: Invalidate cache entries manually
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

    Args:
        strategy: The invalidation strategy to use
        pattern: The pattern to match for pattern-based invalidation
        dependencies: The dependencies for dependency-based invalidation
        version: The version for version-based invalidation
        ttl: The TTL in seconds for TTL-based invalidation
        max_size: The maximum size for LRU-based invalidation
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

    Args:
        cache_manager: The cache manager to use, or None to use the global one
        namespace: The namespace to use for cache keys
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

    def add_rule(self, key: str, rule: CacheInvalidationRule) -> None:
        """Add a cache invalidation rule.

        Args:
            key: The key to add the rule for
            rule: The rule to add
        """
        self.rules[key] = rule

        # Set up dependencies
        if rule.strategy == InvalidationStrategy.DEPENDENCY:
            for dependency in rule.dependencies:
                if dependency not in self.dependencies:
                    self.dependencies[dependency] = set()
                self.dependencies[dependency].add(key)

        # Set up version
        if rule.strategy == InvalidationStrategy.VERSION:
            if rule.version is not None:
                self.versions[key] = rule.version

        # Set up LRU
        if rule.strategy == InvalidationStrategy.LRU:
            if rule.max_size is not None:
                self.size_limits[key] = rule.max_size
                self.current_sizes[key] = 0

    def remove_rule(self, key: str) -> None:
        """Remove a cache invalidation rule.

        Args:
            key: The key to remove the rule for
        """
        if key in self.rules:
            rule = self.rules[key]

            # Clean up dependencies
            if rule.strategy == InvalidationStrategy.DEPENDENCY:
                for dependency in rule.dependencies:
                    if dependency in self.dependencies:
                        self.dependencies[dependency].discard(key)
                        if not self.dependencies[dependency]:
                            del self.dependencies[dependency]

            # Clean up version
            if rule.strategy == InvalidationStrategy.VERSION:
                if key in self.versions:
                    del self.versions[key]

            # Clean up LRU
            if rule.strategy == InvalidationStrategy.LRU:
                if key in self.size_limits:
                    del self.size_limits[key]
                if key in self.current_sizes:
                    del self.current_sizes[key]

            del self.rules[key]

    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: The key to invalidate
        """
        full_key = f"{self.namespace}:{key}"
        self.cache_manager.delete(full_key)

        # Invalidate dependencies
        if key in self.dependencies:
            for dependent in self.dependencies[key]:
                self.invalidate(dependent)

    def invalidate_by_pattern(self, pattern: str) -> None:
        """Invalidate cache entries by pattern.

        Args:
            pattern: The pattern to match
        """
        # Find all keys that match the pattern
        for key, rule in self.rules.items():
            if rule.strategy == InvalidationStrategy.PATTERN:
                if rule.pattern is not None and rule.pattern == pattern:
                    self.invalidate(key)

    def invalidate_by_version(self, key: str, version: str) -> None:
        """Invalidate a cache entry by version.

        Args:
            key: The key to invalidate
            version: The version to check
        """
        if key in self.versions and self.versions[key] != version:
            self.invalidate(key)
            self.versions[key] = version

    def check_ttl(self, key: str) -> bool:
        """Check if a cache entry is expired based on TTL.

        Args:
            key: The key to check

        Returns:
            True if the cache entry is valid, False if it is expired
        """
        if key not in self.rules:
            return True

        rule = self.rules[key]
        if rule.strategy != InvalidationStrategy.TTL or rule.ttl is None:
            return True

        full_key = f"{self.namespace}:{key}"
        if not self.cache_manager.has(full_key):
            return False

        # We can't check the TTL directly, so we'll have to rely on the
        # cache manager's implementation
        return True

    def update_lru(self, key: str) -> None:
        """Update the LRU status for a key.

        Args:
            key: The key to update
        """
        # Skip if the key doesn't exist
        if key not in self.rules:
            return

        rule = self.rules[key]
        if rule.strategy != InvalidationStrategy.LRU:
            return

        self.access_times[key] = time.time()

        # Check if we need to evict entries
        if (
            key in self.size_limits
            and key in self.current_sizes
            and self.current_sizes[key] > self.size_limits[key]
        ):
            # Schedule the eviction to run asynchronously
            asyncio.create_task(self._evict_lru_entries(key))

    async def _evict_lru_entries(self, key: str) -> None:
        """Evict LRU entries for a key.

        Args:
            key: The key to evict entries for
        """
        if key not in self.size_limits or key not in self.current_sizes:
            return

        # Find all entries for this key
        entries = []
        for entry_key, access_time in self.access_times.items():
            if entry_key.startswith(f"{key}:"):
                entries.append((entry_key, access_time))

        # Sort by access time (oldest first)
        entries.sort(key=lambda x: x[1])

        # Evict entries until we're under the limit
        for entry_key, _ in entries:
            if self.current_sizes[key] <= self.size_limits[key]:
                break

            self.invalidate(entry_key)
            self.current_sizes[key] -= 1


class AsyncCacheInvalidator(Generic[T]):
    """Asynchronous cache invalidator.

    An asynchronous cache invalidator is responsible for invalidating cache entries
    based on different strategies.

    Args:
        cache_manager: The cache manager to use, or None to use the global one
        namespace: The namespace to use for cache keys
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

    def add_rule(self, key: str, rule: CacheInvalidationRule) -> None:
        """Add a cache invalidation rule.

        Args:
            key: The key to add the rule for
            rule: The rule to add
        """
        self.rules[key] = rule

        # Set up dependencies
        if rule.strategy == InvalidationStrategy.DEPENDENCY:
            for dependency in rule.dependencies:
                if dependency not in self.dependencies:
                    self.dependencies[dependency] = set()
                self.dependencies[dependency].add(key)

        # Set up version
        if rule.strategy == InvalidationStrategy.VERSION:
            if rule.version is not None:
                self.versions[key] = rule.version

        # Set up LRU
        if rule.strategy == InvalidationStrategy.LRU:
            if rule.max_size is not None:
                self.size_limits[key] = rule.max_size
                self.current_sizes[key] = 0

    def remove_rule(self, key: str) -> None:
        """Remove a cache invalidation rule.

        Args:
            key: The key to remove the rule for
        """
        if key in self.rules:
            rule = self.rules[key]

            # Clean up dependencies
            if rule.strategy == InvalidationStrategy.DEPENDENCY:
                for dependency in rule.dependencies:
                    if dependency in self.dependencies:
                        self.dependencies[dependency].discard(key)
                        if not self.dependencies[dependency]:
                            del self.dependencies[dependency]

            # Clean up version
            if rule.strategy == InvalidationStrategy.VERSION:
                if key in self.versions:
                    del self.versions[key]

            # Clean up LRU
            if rule.strategy == InvalidationStrategy.LRU:
                if key in self.size_limits:
                    del self.size_limits[key]
                if key in self.current_sizes:
                    del self.current_sizes[key]

            del self.rules[key]

    async def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: The key to invalidate
        """
        full_key = f"{self.namespace}:{key}"
        await self.cache_manager.adelete(full_key)

        # Invalidate dependencies
        if key in self.dependencies:
            for dependent in self.dependencies[key]:
                await self.invalidate(dependent)

    async def invalidate_by_pattern(self, pattern: str) -> None:
        """Invalidate cache entries by pattern.

        Args:
            pattern: The pattern to match
        """
        # Find all keys that match the pattern
        for key, rule in self.rules.items():
            if rule.strategy == InvalidationStrategy.PATTERN:
                if rule.pattern is not None and rule.pattern == pattern:
                    await self.invalidate(key)

    async def invalidate_by_version(self, key: str, version: str) -> None:
        """Invalidate a cache entry by version.

        Args:
            key: The key to invalidate
            version: The version to check
        """
        if key in self.versions and self.versions[key] != version:
            await self.invalidate(key)
            self.versions[key] = version

    async def check_ttl(self, key: str) -> bool:
        """Check if a cache entry is expired based on TTL.

        Args:
            key: The key to check

        Returns:
            True if the cache entry is valid, False if it is expired
        """
        if key not in self.rules:
            return True

        rule = self.rules[key]
        if rule.strategy != InvalidationStrategy.TTL or rule.ttl is None:
            return True

        full_key = f"{self.namespace}:{key}"
        if not await self.cache_manager.ahas(full_key):
            return False

        # We can't check the TTL directly, so we'll have to rely on the
        # cache manager's implementation
        return True

    def update_lru(self, key: str) -> None:
        """Update the LRU status for a key.

        Args:
            key: The key to update
        """
        # Skip if the key doesn't exist
        if key not in self.rules:
            return

        rule = self.rules[key]
        if rule.strategy != InvalidationStrategy.LRU:
            return

        self.access_times[key] = time.time()

        # Check if we need to evict entries
        if (
            key in self.size_limits
            and key in self.current_sizes
            and self.current_sizes[key] > self.size_limits[key]
        ):
            # Schedule the eviction to run asynchronously
            asyncio.create_task(self._evict_lru_entries(key))

    async def _evict_lru_entries(self, key: str) -> None:
        """Evict LRU entries for a key.

        Args:
            key: The key to evict entries for
        """
        if key not in self.size_limits or key not in self.current_sizes:
            return

        # Find all entries for this key
        entries = []
        for entry_key, access_time in self.access_times.items():
            if entry_key.startswith(f"{key}:"):
                entries.append((entry_key, access_time))

        # Sort by access time (oldest first)
        entries.sort(key=lambda x: x[1])

        # Evict entries until we're under the limit
        for entry_key, _ in entries:
            if self.current_sizes[key] <= self.size_limits[key]:
                break

            await self.invalidate(entry_key)
            self.current_sizes[key] -= 1


def _create_key(
    func: Callable[..., Any],
    args: tuple,
    kwargs: dict,
    namespace: str,
    key_prefix: Optional[str] = None,
    key_generator: Optional[Callable[..., str]] = None,
) -> str:
    """Create a cache key for a function call.

    Args:
        func: The function being called
        args: The positional arguments
        kwargs: The keyword arguments
        namespace: The namespace to use for the key
        key_prefix: An optional prefix for the key
        key_generator: An optional function to generate the key

    Returns:
        The cache key
    """
    if key_generator is not None:
        key = key_generator(func, args, kwargs)
    else:
        # Get the function's module and name
        module = func.__module__
        name = func.__qualname__

        # Create a string representation of the arguments
        arg_str = str(args) + str(sorted(kwargs.items()))

        # Create a hash of the arguments
        arg_hash = hashlib.md5(arg_str.encode()).hexdigest()

        # Create the key
        key = f"{module}.{name}:{arg_hash}"

    # Add the prefix if provided
    if key_prefix is not None:
        key = f"{key_prefix}:{key}"

    # Add the namespace
    return f"{namespace}:{key}"


def cached(
    ttl: Optional[int] = None,
    namespace: str = "default",
    key_prefix: Optional[str] = None,
    key_generator: Optional[Callable[..., str]] = None,
    cache_manager: Optional[CacheManager] = None,
    invalidator: Optional[CacheInvalidator] = None,
    invalidation_rule: Optional[CacheInvalidationRule] = None,
) -> Callable[[F], F]:
    """Cache the result of a function call.

    Args:
        ttl: The time-to-live in seconds, or None for no expiration
        namespace: The namespace to use for cache keys
        key_prefix: An optional prefix for cache keys
        key_generator: An optional function to generate cache keys
        cache_manager: The cache manager to use, or None to use the global one
        invalidator: The cache invalidator to use, or None to use a new one
        invalidation_rule: The invalidation rule to use, or None to use TTL

    Returns:
        A decorator that caches the result of a function call
    """

    def decorator(func: F) -> F:
        """Decorate a function to cache its result.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Get the signature of the function
        sig = inspect.signature(func)

        # Create a cache invalidator if needed
        nonlocal invalidator
        if invalidator is None:
            invalidator = CacheInvalidator(
                cache_manager=cache_manager, namespace=namespace
            )

        # Create an invalidation rule if needed
        nonlocal invalidation_rule
        if invalidation_rule is None:
            invalidation_rule = CacheInvalidationRule(
                strategy=InvalidationStrategy.TTL, ttl=ttl
            )

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrap the function to cache its result.

            Args:
                *args: The positional arguments
                **kwargs: The keyword arguments

            Returns:
                The result of the function call
            """
            # Create a cache key
            key = _create_key(func, args, kwargs, namespace, key_prefix, key_generator)

            # Get the cache manager
            cm = cache_manager or get_cache_manager()

            # Check if the result is cached
            result = cm.get(key)
            if result is not None:
                # Update LRU information
                if invalidator is not None:
                    invalidator.update_lru(key)

                return result

            # Call the function
            result = func(*args, **kwargs)

            # Cache the result
            cm.set(key, result, ttl)

            # Add an invalidation rule if needed
            if invalidator is not None and invalidation_rule is not None:
                invalidator.add_rule(key, invalidation_rule)

            return result

        return cast(F, wrapper)

    return decorator


def async_cached(
    ttl: Optional[int] = None,
    namespace: str = "default",
    key_prefix: Optional[str] = None,
    key_generator: Optional[Callable[..., str]] = None,
    cache_manager: Optional[AsyncCacheManager] = None,
    invalidator: Optional[AsyncCacheInvalidator] = None,
    invalidation_rule: Optional[CacheInvalidationRule] = None,
) -> Callable[[F], F]:
    """Cache the result of an asynchronous function call.

    Args:
        ttl: The time-to-live in seconds, or None for no expiration
        namespace: The namespace to use for cache keys
        key_prefix: An optional prefix for cache keys
        key_generator: An optional function to generate cache keys
        cache_manager: The cache manager to use, or None to use the global one
        invalidator: The cache invalidator to use, or None to use a new one
        invalidation_rule: The invalidation rule to use, or None to use TTL

    Returns:
        A decorator that caches the result of an asynchronous function call
    """

    def decorator(func: F) -> F:
        """Decorate an asynchronous function to cache its result.

        Args:
            func: The function to decorate

        Returns:
            The decorated function
        """
        # Get the signature of the function
        sig = inspect.signature(func)

        # Create a cache invalidator if needed
        nonlocal invalidator
        if invalidator is None:
            invalidator = AsyncCacheInvalidator(
                cache_manager=cache_manager, namespace=namespace
            )

        # Create an invalidation rule if needed
        nonlocal invalidation_rule
        if invalidation_rule is None:
            invalidation_rule = CacheInvalidationRule(
                strategy=InvalidationStrategy.TTL, ttl=ttl
            )

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrap the function to cache its result.

            Args:
                *args: The positional arguments
                **kwargs: The keyword arguments

            Returns:
                The result of the function call
            """
            # Create a cache key
            key = _create_key(func, args, kwargs, namespace, key_prefix, key_generator)

            # Get the cache manager
            cm = cache_manager or get_async_cache_manager()

            # Check if the result is cached
            result = await cm.aget(key)
            if result is not None:
                # Update LRU information
                if invalidator is not None:
                    invalidator.update_lru(key)

                return result

            # Call the function
            result = await func(*args, **kwargs)

            # Cache the result
            await cm.aset(key, result, ttl)

            # Add an invalidation rule if needed
            if invalidator is not None and invalidation_rule is not None:
                invalidator.add_rule(key, invalidation_rule)

            return result

        return cast(F, wrapper)

    return decorator


def clear_cache(
    namespace: str = "default",
    cache_manager: Optional[Union[CacheManager, AsyncCacheManager]] = None,
) -> None:
    """Clear the cache for a namespace.

    Args:
        namespace: The namespace to clear
        cache_manager: The cache manager to use, or None to use the global one
    """
    if cache_manager is None:
        # Try both synchronous and asynchronous cache managers
        try:
            cache_manager = get_cache_manager()
            cache_manager.clear()
        except Exception:
            pass

        try:
            cache_manager = get_async_cache_manager()
            # We can't await here, so we'll have to rely on the
            # cache manager's implementation
            cache_manager.aclear()  # type: ignore
        except Exception:
            pass
    else:
        # Use the provided cache manager
        if isinstance(cache_manager, AsyncCacheManager):
            # We can't await here, so we'll have to rely on the
            # cache manager's implementation
            cache_manager.aclear()  # type: ignore
        else:
            cache_manager.clear()


def invalidate_cache(
    key: str,
    namespace: str = "default",
    cache_manager: Optional[Union[CacheManager, AsyncCacheManager]] = None,
) -> None:
    """Invalidate a cache entry.

    Args:
        key: The key to invalidate
        namespace: The namespace to use for cache keys
        cache_manager: The cache manager to use, or None to use the global one
    """
    full_key = f"{namespace}:{key}"

    if cache_manager is None:
        # Try both synchronous and asynchronous cache managers
        try:
            cache_manager = get_cache_manager()
            cache_manager.delete(full_key)
        except Exception:
            pass

        try:
            cache_manager = get_async_cache_manager()
            # We can't await here, so we'll have to rely on the
            # cache manager's implementation
            cache_manager.adelete(full_key)  # type: ignore
        except Exception:
            pass
    else:
        # Use the provided cache manager
        if isinstance(cache_manager, AsyncCacheManager):
            # We can't await here, so we'll have to rely on the
            # cache manager's implementation
            cache_manager.adelete(full_key)  # type: ignore
        else:
            cache_manager.delete(full_key)


def initialize_cache(
    cache_type: str = "memory",
    cache_directory: Optional[str] = None,
    cache_url: Optional[str] = None,
    cache_options: Optional[Dict[str, Any]] = None,
) -> None:
    """Initialize the cache system.

    Args:
        cache_type: The type of cache to use (memory, file, redis, etc.)
        cache_directory: The directory to use for file-based caching
        cache_url: The URL to use for distributed caching
        cache_options: Additional options for the cache backend
    """
    # This is a placeholder for now, as we need to implement the actual
    # initialization logic in the cache module
    logger.info(f"Initializing cache system with type: {cache_type}")
