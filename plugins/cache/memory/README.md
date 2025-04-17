# Memory Cache Provider

A simple in-memory cache implementation for the PepperPy framework.

## Features

- Fast in-memory key-value storage
- Time-to-live (TTL) expiration
- Tag-based cache invalidation
- Metadata support with advanced search capabilities
- Configurable maximum entries
- Automatic expiration cleanup

## Configuration

The provider supports the following configuration options:

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `max_entries` | integer | Maximum number of entries to store in cache | 10000 |
| `default_ttl` | integer | Default time-to-live in seconds | 3600 |

## Usage via Framework

```python
from pepperpy import PepperPy

# Initialize PepperPy with memory cache
pepper = PepperPy().with_cache("memory", max_entries=5000, default_ttl=1800)

async with pepper:
    # Set a value in cache with metadata
    result = await pepper.cache.execute({
        "task": "set",
        "key": "user-123",
        "value": {"name": "John Doe", "email": "john@example.com"},
        "ttl": 300,  # 5 minutes
        "tags": ["user", "profile"],
        "metadata": {
            "user_id": 123,
            "role": "admin",
            "last_active": 1623456789,
            "is_premium": True
        }
    })
    
    # Search for entries by metadata
    result = await pepper.cache.execute({
        "task": "search",
        "query": {
            "role": "admin",
            "is_premium": True
        }
    })
    
    # Search with advanced operators
    result = await pepper.cache.execute({
        "task": "search",
        "query": {
            "last_active": {"$gt": 1623000000},
            "user_id": {"$in": [123, 456, 789]}
        }
    })
    
    # Get a value from cache
    result = await pepper.cache.execute({
        "task": "get",
        "key": "user-123",
        "default": {}
    })
    
    # Invalidate all entries with a specific tag
    result = await pepper.cache.execute({
        "task": "invalidate_tag",
        "tag": "user"
    })
    
    # Purge only expired entries
    result = await pepper.cache.execute({
        "task": "clear",
        "purge_only": True
    })
```

## Direct Adapter Pattern (for Development/Testing)

```python
from plugins.cache.memory.provider import MemoryCacheProvider

# Create adapter directly
adapter = MemoryCacheProvider(max_entries=1000, default_ttl=60)

async with adapter:
    # Set a value with metadata
    result = await adapter.execute({
        "task": "set",
        "key": "test-key",
        "value": "test-value",
        "metadata": {
            "category": "test",
            "importance": 5
        }
    })
    
    # Search for entries by metadata
    result = await adapter.execute({
        "task": "search",
        "query": {
            "category": "test", 
            "importance": {"$gt": 3}
        }
    })
    
    # Work with search results
    if result["status"] == "success":
        for entry in result["results"]:
            print(f"Found key: {entry['key']}, value: {entry['value']}")
```

## CLI Usage

The provider includes a CLI tool for direct access:

```bash
# Set a value with metadata
python -m plugins.cache.memory.cli set --key "user-123" --value "John Doe" --metadata '{"role":"admin","is_premium":true}'

# Search by metadata (exact match)
python -m plugins.cache.memory.cli search --query '{"role":"admin"}'

# Search by metadata with operators
python -m plugins.cache.memory.cli search --query '{"is_premium":true,"last_login":{"$gt":1623000000}}'

# Get a value
python -m plugins.cache.memory.cli get --key "user-123"

# Set with tags
python -m plugins.cache.memory.cli set --key "tagged-key" --value "value" --tags "tag1,tag2"

# Invalidate tag
python -m plugins.cache.memory.cli invalidate_tag --tag "tag1" 

# Clear cache
python -m plugins.cache.memory.cli clear

# Purge only expired entries
python -m plugins.cache.memory.cli clear --purge-only
```

## Operations

The provider supports the following operations:

### `get`
Retrieve a value from the cache.

**Parameters:**
- `key` (required): The cache key to retrieve
- `default`: Default value if key not found

**Returns:**
- `status`: "success" or "error"
- `value`: The cached value or default value
- `found`: Boolean indicating if key was found

### `set`
Store a value in the cache.

**Parameters:**
- `key` (required): The cache key
- `value` (required): Value to cache
- `ttl`: Time to live in seconds
- `tags`: List of tags to associate with key
- `metadata`: Additional metadata to store

**Returns:**
- `status`: "success" or "error"
- `message`: Operation result message

### `search`
Search for cache entries by metadata criteria.

**Parameters:**
- `query` (required): Dictionary of metadata keys and values to match

**Operators:**
- `{"field": value}`: Exact match
- `{"field": {"$gt": value}}`: Greater than
- `{"field": {"$lt": value}}`: Less than
- `{"field": {"$in": [value1, value2]}}`: In list
- `{"field": {"$exists": true}}`: Field exists

**Returns:**
- `status`: "success" or "error"
- `results`: List of matching entries (key, value, metadata)
- `count`: Number of matching entries

### `delete`
Delete a key from the cache.

**Parameters:**
- `key` (required): The cache key to delete

**Returns:**
- `status`: "success" or "error"
- `message`: Operation result message

### `invalidate_tag`
Invalidate all cache entries with a specific tag.

**Parameters:**
- `tag` (required): Tag to invalidate

**Returns:**
- `status`: "success" or "error"
- `message`: Operation result message

### `clear`
Clear all entries from the cache or purge only expired entries.

**Parameters:**
- `purge_only`: (Optional) If true, removes only expired entries instead of clearing all

**Returns:**
- `status`: "success" or "error"
- `message`: Operation result message
- `purged_count`: (Only when purge_only=true) Number of entries purged

## Internal Cache Management

The provider automatically manages cache entries:

1. **Lazy Expiration**: Expired entries are removed when accessed
2. **Proactive Purging**: Expired entries are purged before capacity errors
3. **Manual Purging**: Use the "clear" task with purge_only=true to remove expired entries

When capacity is reached, the provider attempts to remove expired entries before failing. 