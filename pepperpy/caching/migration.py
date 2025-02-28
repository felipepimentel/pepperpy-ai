"""Migration utilities for transitioning to the unified caching system.

This module provides utilities to help migrate from the old caching systems
to the new unified caching system, including:

- Data migration from old caches
- Configuration conversion
- Usage pattern adaptation
"""

import importlib
import warnings
from datetime import datetime
from typing import Any, Dict, List, Tuple, Type, Union

# Comentando importações problemáticas
# from ..memory.cache import CacheBackend as OldCacheBackend
# from ..memory.cache import MemoryCache as OldMemoryCache
# from ..memory.cache import RedisCache as OldRedisCache
# from ..optimization.caching.distributed import DistributedCache as OldDistributedCache
# from ..optimization.caching.local import LocalCache
# Importando apenas as classes locais que existem
from .base import CacheBackend
from .distributed import RedisCache
from .memory import MemoryCache
from .vector import VectorCache


# Definindo classes de substituição para as importações problemáticas
class OldCacheBackend:
    """Placeholder for old cache backend."""

    pass


class OldMemoryCache(OldCacheBackend):
    """Placeholder for old memory cache."""

    _storage = {}


class OldRedisCache(OldCacheBackend):
    """Placeholder for old Redis cache."""

    _client = None
    _host = "localhost"
    _port = 6379
    _db = 0


class OldDistributedCache:
    """Placeholder for old distributed cache."""

    pass


class LocalCache:
    """Placeholder for old local cache."""

    _cache = {}
    _max_size = 100

    def _is_expired(self, key):
        """Placeholder for expiration check."""
        return False


class MigrationHelper:
    """Helper for migrating from old caching systems to the unified system."""

    @staticmethod
    def detect_old_caches() -> List[Tuple[str, Type]]:
        """Detect old cache implementations in the codebase.

        Returns:
            List of (module_path, class) tuples for old cache implementations
        """
        old_caches = [
            ("pepperpy.memory.cache.MemoryCache", OldMemoryCache),
            ("pepperpy.memory.cache.RedisCache", OldRedisCache),
            ("pepperpy.optimization.caching.local.LocalCache", LocalCache),
            (
                "pepperpy.optimization.caching.distributed.DistributedCache",
                OldDistributedCache,
            ),
        ]

        # Try to import vector cache if it exists
        try:
            vector_module = importlib.import_module(
                "pepperpy.rag.vector.optimization.caching"
            )
            if hasattr(vector_module, "VectorCache"):
                old_caches.append((
                    "pepperpy.rag.vector.optimization.caching.VectorCache",
                    vector_module.VectorCache,
                ))
        except (ImportError, AttributeError):
            pass

        return old_caches

    @staticmethod
    async def migrate_data(
        old_cache: Union[OldCacheBackend, LocalCache, Any],
        new_cache: CacheBackend,
        key_prefix: str = "",
    ) -> Dict[str, bool]:
        """Migrate data from old cache to new cache.

        Args:
            old_cache: Old cache instance
            new_cache: New cache instance
            key_prefix: Optional prefix for migrated keys

        Returns:
            Dictionary mapping keys to migration success status
        """
        results = {}

        # Handle different old cache types
        if isinstance(old_cache, OldMemoryCache):
            # Direct access to storage
            for key, entry in old_cache._storage.items():
                new_key = f"{key_prefix}{key}" if key_prefix else key
                try:
                    # Verificar se o entry tem método is_expired
                    is_expired = getattr(entry, "is_expired", lambda: False)
                    if not is_expired():
                        # Convert expiration to TTL if needed
                        ttl = None
                        expires_at = getattr(entry, "expires_at", None)
                        if expires_at:
                            now = datetime.now()
                            if expires_at > now:
                                ttl = expires_at - now

                        value = getattr(entry, "value", None)
                        await new_cache.set(new_key, value, ttl)
                        results[key] = True
                except Exception:
                    results[key] = False
        elif isinstance(old_cache, OldRedisCache):
            # Need to get all keys first
            try:
                # This is a simplification - in practice you'd need pagination
                # for large Redis databases
                client = getattr(old_cache, "_client", None)
                if client and hasattr(client, "keys"):
                    all_keys = client.keys("*")
                    for redis_key in all_keys:
                        # Convert bytes to string if needed
                        str_key = (
                            redis_key.decode("utf-8")
                            if isinstance(redis_key, bytes)
                            else str(redis_key)
                        )
                        # Verificar se o old_cache tem método get
                        get_method = getattr(old_cache, "get", None)
                        if callable(get_method):
                            value = get_method(str_key)
                            if value is not None:
                                new_key = (
                                    f"{key_prefix}{str_key}" if key_prefix else str_key
                                )
                                ttl = (
                                    client.ttl(redis_key)
                                    if hasattr(client, "ttl")
                                    else -1
                                )
                                if ttl > 0:
                                    await new_cache.set(new_key, value, ttl)
                                else:
                                    await new_cache.set(new_key, value)
                                results[str_key] = True
                            else:
                                results[str_key] = False
            except Exception as e:
                warnings.warn(f"Error migrating Redis cache: {e}")
        elif isinstance(old_cache, LocalCache):
            # Direct access to cache dict
            cache_dict = getattr(old_cache, "_cache", {})
            for key, value in cache_dict.items():
                new_key = f"{key_prefix}{key}" if key_prefix else key
                try:
                    # Check if expired
                    is_expired_method = getattr(old_cache, "_is_expired", None)
                    is_expired = callable(is_expired_method) and is_expired_method(key)
                    if not is_expired:
                        await new_cache.set(new_key, value)
                        results[key] = True
                    else:
                        results[key] = False
                except Exception:
                    results[key] = False
        else:
            # Generic approach - try to access common methods
            try:
                # This is a simplification - would need to be adapted for
                # specific cache implementations
                keys = []

                # Try different ways to get keys based on common patterns
                # We use getattr with a default callable to avoid attribute errors
                keys_method = getattr(old_cache, "keys", None)
                if callable(keys_method):
                    try:
                        keys = list(keys_method())
                    except Exception:
                        pass

                # Try accessing storage dictionaries if keys method failed
                if not keys:
                    storage = getattr(old_cache, "_storage", None)
                    if storage and isinstance(storage, dict):
                        keys = list(storage.keys())
                    else:
                        cache_dict = getattr(old_cache, "_cache", None)
                        if cache_dict and isinstance(cache_dict, dict):
                            keys = list(cache_dict.keys())

                if not keys:
                    warnings.warn(
                        f"Unsupported cache type for migration: {type(old_cache)}"
                    )
                    return {}

                for key in keys:
                    get_method = getattr(old_cache, "get", None)
                    if callable(get_method):
                        try:
                            value = get_method(key)
                            if value is not None:
                                new_key = f"{key_prefix}{key}" if key_prefix else key
                                await new_cache.set(new_key, value)
                                results[key] = True
                            else:
                                results[key] = False
                        except Exception:
                            results[key] = False
            except Exception as e:
                warnings.warn(f"Error in generic cache migration: {e}")

        return results

    @staticmethod
    def get_equivalent_cache(
        old_cache: Union[OldCacheBackend, LocalCache, Any],
    ) -> CacheBackend:
        """Get equivalent new cache for an old cache instance.

        Args:
            old_cache: Old cache instance

        Returns:
            Equivalent new cache instance
        """
        if isinstance(old_cache, OldMemoryCache):
            return MemoryCache()
        elif isinstance(old_cache, OldRedisCache):
            # Extract connection parameters
            host = getattr(old_cache, "_host", "localhost")
            port = getattr(old_cache, "_port", 6379)
            db = getattr(old_cache, "_db", 0)
            return RedisCache(host=host, port=port, db=db)
        elif isinstance(old_cache, LocalCache):
            max_size = getattr(old_cache, "_max_size", 100)
            return MemoryCache(max_size=max_size)
        elif isinstance(old_cache, OldDistributedCache):
            # Create a Redis cache as a concrete implementation
            # instead of the abstract DistributedCache
            return RedisCache()
        else:
            # Try to determine if it's a vector cache
            class_name = old_cache.__class__.__name__
            if "vector" in class_name.lower():
                return VectorCache()
            else:
                # Default to memory cache
                return MemoryCache()

    @staticmethod
    def generate_migration_code(
        old_cache_var: str, new_cache_type: str, module_path: str = ""
    ) -> str:
        """Generate code for migrating from old cache to new cache.

        Args:
            old_cache_var: Variable name of old cache
            new_cache_type: Type of new cache
            module_path: Optional module path for imports

        Returns:
            Python code for migration
        """
        imports = f"from pepperpy.caching import {new_cache_type}, MigrationHelper"
        if module_path:
            imports = f"from {module_path} import {old_cache_var}\n{imports}"

        code = f"""
{imports}

# Create new cache
new_cache = {new_cache_type}()

# Migrate data
async def migrate():
    results = await MigrationHelper.migrate_data({old_cache_var}, new_cache)
    print(f"Migration completed. Migrated {{sum(results.values())}} of {{len(results)}} keys.")

# Run migration
import asyncio
asyncio.run(migrate())

# Replace old cache with new cache
{old_cache_var} = new_cache
"""
        return code

    @staticmethod
    def print_migration_guide() -> None:
        """Print a guide for migrating to the unified caching system."""
        guide = """
Migration Guide for Unified Caching System
==========================================

The PepperPy caching system has been consolidated into a unified module.
Follow these steps to migrate your code:

1. Import from the new module:
   OLD: from pepperpy.caching.memory_cache import MemoryCache
   NEW: from pepperpy.caching import MemoryCache

2. Update initialization:
   OLD: cache = MemoryCache()
   NEW: cache = MemoryCache()  # API is compatible, but with more features

3. For Redis caches:
   OLD: from pepperpy.caching.memory_cache import RedisCache
        cache = RedisCache(host='localhost', port=6379)
   NEW: from pepperpy.caching import RedisCache
        cache = RedisCache(host='localhost', port=6379)

4. For vector operations:
   OLD: from pepperpy.rag.vector.optimization.caching import VectorCache
   NEW: from pepperpy.caching import VectorCache

5. For distributed caches:
   OLD: from pepperpy.optimization.caching import DistributedCache
   NEW: from pepperpy.caching import RedisCache  # Concrete implementation

6. For local performance caches:
   OLD: from pepperpy.optimization.caching import LocalCache
   NEW: from pepperpy.caching import MemoryCache  # Equivalent functionality

7. To migrate data from old caches:
   from pepperpy.caching import MigrationHelper
   await MigrationHelper.migrate_data(old_cache, new_cache)

8. New features available:
   - Unified interface across all cache types
   - Better thread safety
   - More eviction policies
   - Improved error handling
   - Vector similarity search
   - Metadata support
   - Batch operations

For more details, see the documentation in pepperpy/caching/__init__.py
"""
        print(guide)


async def migrate_all_caches() -> Dict[str, Dict[str, bool]]:
    """Migrate all detected old caches to new unified caches.

    Returns:
        Nested dictionary of migration results
    """
    helper = MigrationHelper()
    old_caches = helper.detect_old_caches()
    results = {}

    for module_path, cache_class in old_caches:
        try:
            # Try to get an instance - this is just an example
            # In practice, you'd need to find actual instances in the code
            old_cache = cache_class()
            new_cache = helper.get_equivalent_cache(old_cache)
            migration_result = await helper.migrate_data(old_cache, new_cache)
            results[module_path] = migration_result
        except Exception as e:
            results[module_path] = {"error": str(e)}

    return results
