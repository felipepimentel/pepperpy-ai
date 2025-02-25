# Pepperpy Caching System

A unified caching system that provides configurable policies, centralized metrics, and support for multiple storage backends.

## Features

- Multiple storage backends (Memory, Redis)
- Configurable cache policies (LRU, TTL)
- Centralized metrics collection
- Pattern-based invalidation
- Metadata support
- Comprehensive error handling

## Quick Start

```python
from pepperpy.caching.stores import MemoryStore
from pepperpy.caching.policies import LRUPolicy

# Create a memory store with LRU policy
policy = LRUPolicy(max_size=1000)
store = MemoryStore(policy=policy)

# Basic operations
await store.set("key", "value", ttl=60)
value = await store.get("key")
await store.delete("key")

# With metadata
metadata = {"version": 1, "author": "user"}
await store.set("key", "value", metadata=metadata)
stored_metadata = await store.get_metadata("key")
```

## Redis Backend

```python
from pepperpy.caching.stores import RedisStore

# Create a Redis store
store = RedisStore(
    redis_url="redis://localhost:6379/0",
    prefix="myapp:",
)

# Operations work the same as memory store
await store.set("key", "value")
value = await store.get("key")
```

## Cache Policies

### LRU (Least Recently Used)
```python
from pepperpy.caching.policies import LRUPolicy

policy = LRUPolicy(max_size=1000)
store = MemoryStore(policy=policy)

# Policy will automatically evict least recently used items
await store.set("key1", "value1")
await store.set("key2", "value2")
# ... after 1000 items, oldest ones are evicted
```

### TTL (Time To Live)
```python
# Set TTL in seconds
await store.set("key", "value", ttl=60)
```

## Metrics

```python
from pepperpy.caching.metrics import CacheMetrics

metrics = store.get_stats()
print(f"Hit ratio: {metrics['hit_ratio']}")
print(f"Average latency: {metrics['avg_get_latency']}ms")
```

## Error Handling

```python
from pepperpy.caching.errors import CacheError, CacheKeyError

try:
    await store.get(123)  # Invalid key type
except CacheKeyError as e:
    print(f"Invalid key: {e}")
except CacheError as e:
    print(f"Cache error: {e}")
```

## Contributing

1. Follow Google-style docstrings
2. Add tests for new features
3. Run tests with `pytest tests/`
4. Format code with `black` and `ruff` 