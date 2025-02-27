# PepperPy Unified Caching System

This module provides a comprehensive caching system for all PepperPy components, with specialized implementations for different use cases.

## Overview

The unified caching system consolidates previously fragmented caching implementations into a single, coherent module with a consistent API. This system replaces:

- `memory/cache.py` (agent-specific cache)
- `core/resources/cache.py` (resource cache)
- `optimization/caching/` (performance cache)
- `rag/vector/optimization/caching.py` (vector cache)

## Components

### Base Functionality (`base.py`)

- `CacheEntry`: Container for cached values with metadata
- `Serializer`: Interface for value serialization/deserialization
- `CachePolicy`: Interface for cache eviction policies
- `CacheBackend`: Interface for storage backends
- `Cache`: High-level cache interface

### Memory Caching (`memory.py`)

- `MemoryCache`: In-memory cache implementation
- Eviction policies:
  - `LRUPolicy`: Least Recently Used
  - `LFUPolicy`: Least Frequently Used
  - `FIFOPolicy`: First In First Out
  - `RandomPolicy`: Random eviction

### Distributed Caching (`distributed.py`)

- `DistributedCache`: Base class for distributed cache implementations
- `RedisCache`: Redis-based distributed cache implementation
  - Cluster support
  - Pub/sub capabilities
  - Serialization options

### Vector Caching (`vector.py`)

- `VectorCache`: Specialized cache for vector embeddings
  - Similarity-based retrieval
  - Batch operations
  - Metadata support

### Migration Utilities (`migration.py`)

- `MigrationHelper`: Utilities for migrating from old caching systems
  - Data migration
  - Configuration conversion
  - Usage pattern adaptation

## Usage Examples

### Basic Memory Cache

```python
from pepperpy.caching import MemoryCache

# Create a memory cache
cache = MemoryCache(max_size=1000)

# Set a value with TTL
await cache.set("key1", "value1", ttl=300)  # 5 minutes

# Get a value
value = await cache.get("key1")

# Check if a key exists
exists = await cache.contains("key1")

# Delete a key
deleted = await cache.delete("key1")

# Clear the cache
await cache.clear()
```

### Redis Cache

```python
from pepperpy.caching import RedisCache

# Create a Redis cache
cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    password="optional_password"
)

# Set a value with TTL
await cache.set("key1", "value1", ttl=300)

# Publish a message
await cache.publish("channel1", {"message": "Hello World"})

# Subscribe to a channel
pubsub = cache.subscribe("channel1")
```

### Vector Cache

```python
import numpy as np
from pepperpy.caching import VectorCache

# Create a vector cache
cache = VectorCache(max_size=10000, similarity_threshold=0.9)

# Store vectors
vector1 = np.array([0.1, 0.2, 0.3])
vector2 = np.array([0.2, 0.3, 0.4])
await cache.set("vec1", vector1)
await cache.set("vec2", vector2)

# Find similar vectors
similar = await cache.find_similar(vector1, top_k=5)

# Store metadata
await cache.set_metadata("vec1", {"source": "document1", "importance": 0.8})

# Batch operations
vectors = {
    "vec3": np.array([0.3, 0.4, 0.5]),
    "vec4": np.array([0.4, 0.5, 0.6])
}
await cache.batch_set(vectors, ttl=3600)
```

### Migration from Old Caches

```python
from pepperpy.caching import MigrationHelper, MemoryCache
from pepperpy.memory.cache import MemoryCache as OldMemoryCache

# Create old and new caches
old_cache = OldMemoryCache()
new_cache = MemoryCache()

# Migrate data
results = await MigrationHelper.migrate_data(old_cache, new_cache)
print(f"Migrated {sum(results.values())} of {len(results)} keys")

# Generate migration code
code = MigrationHelper.generate_migration_code(
    old_cache_var="my_cache",
    new_cache_type="MemoryCache",
    module_path="my_module"
)
print(code)

# Print migration guide
MigrationHelper.print_migration_guide()
```

## Best Practices

1. **Choose the right cache type** for your use case:
   - `MemoryCache` for local, in-process caching
   - `RedisCache` for distributed, cross-process caching
   - `VectorCache` for embedding and similarity-based caching

2. **Set appropriate TTLs** to prevent stale data:
   ```python
   # 5 minutes TTL
   await cache.set("key", value, ttl=300)
   
   # 1 hour TTL
   from datetime import timedelta
   await cache.set("key", value, ttl=timedelta(hours=1))
   ```

3. **Use namespaces** to avoid key collisions:
   ```python
   from pepperpy.caching import Cache, MemoryCache
   
   backend = MemoryCache()
   user_cache = Cache(backend, namespace="users")
   config_cache = Cache(backend, namespace="config")
   
   await user_cache.set("123", user_data)  # Actual key: "users:123"
   await config_cache.set("api", api_config)  # Actual key: "config:api"
   ```

4. **Handle cache misses gracefully**:
   ```python
   value = await cache.get("key")
   if value is None:
       # Cache miss - compute value and update cache
       value = compute_expensive_value()
       await cache.set("key", value)
   ```

5. **Monitor cache performance**:
   ```python
   # For MemoryCache
   hit_ratio = cache.hit_ratio
   size = cache.size
   print(f"Cache hit ratio: {hit_ratio:.2f}, Size: {size}")
   ``` 