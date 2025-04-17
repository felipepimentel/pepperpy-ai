"""Test for memory cache provider."""

import pytest

# Import directly for testing purposes
from pepperpy.cache.provider import CacheError
from plugins.cache.memory.provider import MemoryCacheProvider


@pytest.mark.asyncio
async def test_memory_cache_basic():
    """Test basic functionality of memory cache provider."""
    provider = MemoryCacheProvider(max_entries=10000, default_ttl=3600)

    async with provider:
        await provider.initialize()
        # Set a value
        result = await provider.execute(
            {"task": "set", "key": "test-key", "value": "test-value"}
        )
        assert result["status"] == "success"
        assert result["message"] == "Value cached"

        # Get the value
        result = await provider.execute({"task": "get", "key": "test-key"})
        assert result["status"] == "success"
        assert result["value"] == "test-value"
        assert result["found"] is True
        assert "value" in result


@pytest.mark.asyncio
async def test_memory_cache_ttl():
    """Test TTL functionality of memory cache provider."""
    provider = MemoryCacheProvider(default_ttl=1)

    async with provider:
        await provider.initialize()
        # Set a value with 1 second TTL
        result = await provider.execute(
            {"task": "set", "key": "ttl-key", "value": "ttl-value", "ttl": 1}
        )
        assert result["status"] == "success"
        assert result["message"] == "Value cached"

        # Get it immediately
        result = await provider.execute({"task": "get", "key": "ttl-key"})
        assert result["status"] == "success"
        assert result["found"] is True
        assert result["value"] == "ttl-value"

        # Wait for expiration
        import asyncio

        await asyncio.sleep(1.1)

        # Get it after expiration
        result = await provider.execute({"task": "get", "key": "ttl-key"})
        assert result["status"] == "success"
        assert result["found"] is False
        assert result["value"] is None


@pytest.mark.asyncio
async def test_memory_cache_default_value():
    """Test default value functionality of memory cache provider."""
    provider = MemoryCacheProvider()

    async with provider:
        await provider.initialize()
        # Get non-existent key with default
        result = await provider.execute(
            {"task": "get", "key": "non-existent", "default": "default-value"}
        )
        assert result["status"] == "success"
        assert result["found"] is False
        assert result["value"] == "default-value"


@pytest.mark.asyncio
async def test_memory_cache_max_entries():
    """Test max entries functionality of memory cache provider."""
    provider = MemoryCacheProvider(max_entries=2)

    async with provider:
        await provider.initialize()
        # Set two values
        await provider.execute({"task": "set", "key": "key1", "value": "value1"})
        await provider.execute({"task": "set", "key": "key2", "value": "value2"})

        # Try to set a third value
        result = await provider.execute(
            {"task": "set", "key": "key3", "value": "value3"}
        )
        assert result["status"] == "error"
        assert "capacity" in result["message"].lower()


@pytest.mark.asyncio
async def test_purge_expired_entries():
    """Test purging expired entries functionality."""
    provider = MemoryCacheProvider(default_ttl=1)

    async with provider:
        # Set three values, two with short TTL and one without expiration
        await provider.execute(
            {"task": "set", "key": "expire1", "value": "value1", "ttl": 1}
        )
        await provider.execute(
            {"task": "set", "key": "expire2", "value": "value2", "ttl": 1}
        )
        await provider.execute(
            {"task": "set", "key": "no-expire", "value": "value3", "ttl": None}
        )

        # Wait for expiration
        import asyncio

        await asyncio.sleep(1.1)

        # Purge expired entries
        result = await provider.execute({"task": "clear", "purge_only": True})
        assert result["status"] == "success"
        assert "purged" in result["message"].lower()
        assert result["purged_count"] == 2

        # Verify expired entries are gone but non-expired remain
        result = await provider.execute({"task": "get", "key": "expire1"})
        assert result["found"] is False

        result = await provider.execute({"task": "get", "key": "expire2"})
        assert result["found"] is False

        result = await provider.execute({"task": "get", "key": "no-expire"})
        assert result["found"] is True
        assert result["value"] == "value3"


@pytest.mark.asyncio
async def test_automatic_purge_on_capacity():
    """Test automatic purging when reaching capacity."""
    provider = MemoryCacheProvider(max_entries=2)

    async with provider:
        # Set two values with short TTL
        await provider.execute(
            {"task": "set", "key": "expire1", "value": "value1", "ttl": 1}
        )
        await provider.execute(
            {"task": "set", "key": "expire2", "value": "value2", "ttl": 1}
        )

        # Wait for expiration
        import asyncio

        await asyncio.sleep(1.1)

        # Now try to add a third value - should succeed because expired entries
        # will be purged automatically
        result = await provider.execute(
            {"task": "set", "key": "key3", "value": "value3"}
        )
        assert result["status"] == "success"

        # Verify the new entry exists
        result = await provider.execute({"task": "get", "key": "key3"})
        assert result["found"] is True
        assert result["value"] == "value3"

        # Verify old entries are gone
        result = await provider.execute({"task": "get", "key": "expire1"})
        assert result["found"] is False

        result = await provider.execute({"task": "get", "key": "expire2"})
        assert result["found"] is False


@pytest.mark.asyncio
async def test_metadata_search_simple():
    """Test metadata search functionality with simple queries."""
    provider = MemoryCacheProvider()

    async with provider:
        # Set values with metadata
        await provider.execute(
            {
                "task": "set",
                "key": "user1",
                "value": "John",
                "metadata": {"role": "admin", "active": True, "score": 100},
            }
        )

        await provider.execute(
            {
                "task": "set",
                "key": "user2",
                "value": "Jane",
                "metadata": {"role": "user", "active": True, "score": 80},
            }
        )

        await provider.execute(
            {
                "task": "set",
                "key": "user3",
                "value": "Bob",
                "metadata": {"role": "admin", "active": False, "score": 90},
            }
        )

        # Search by exact match
        result = await provider.execute({"task": "search", "query": {"role": "admin"}})
        assert result["status"] == "success"
        assert result["count"] == 2

        keys = [entry["key"] for entry in result["results"]]
        assert "user1" in keys
        assert "user3" in keys
        assert "user2" not in keys

        # Search with multiple criteria
        result = await provider.execute(
            {"task": "search", "query": {"role": "admin", "active": True}}
        )
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["results"][0]["key"] == "user1"


@pytest.mark.asyncio
async def test_metadata_search_operators():
    """Test metadata search functionality with advanced operators."""
    provider = MemoryCacheProvider()

    async with provider:
        # Set values with metadata
        await provider.execute(
            {
                "task": "set",
                "key": "user1",
                "value": "John",
                "metadata": {
                    "role": "admin",
                    "active": True,
                    "score": 100,
                    "tags": ["premium", "verified"],
                },
            }
        )

        await provider.execute(
            {
                "task": "set",
                "key": "user2",
                "value": "Jane",
                "metadata": {
                    "role": "user",
                    "active": True,
                    "score": 80,
                    "tags": ["verified"],
                },
            }
        )

        await provider.execute(
            {
                "task": "set",
                "key": "user3",
                "value": "Bob",
                "metadata": {"role": "admin", "active": False, "score": 90},
            }
        )

        # Search with $gt operator
        result = await provider.execute(
            {"task": "search", "query": {"score": {"$gt": 90}}}
        )
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["results"][0]["key"] == "user1"

        # Search with $lt operator
        result = await provider.execute(
            {"task": "search", "query": {"score": {"$lt": 90}}}
        )
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["results"][0]["key"] == "user2"

        # Search with $in operator
        result = await provider.execute(
            {"task": "search", "query": {"role": {"$in": ["admin", "superuser"]}}}
        )
        assert result["status"] == "success"
        assert result["count"] == 2

        # Search with $exists operator
        result = await provider.execute(
            {"task": "search", "query": {"tags": {"$exists": True}}}
        )
        assert result["status"] == "success"
        assert result["count"] == 2

        result = await provider.execute(
            {"task": "search", "query": {"tags": {"$exists": False}}}
        )
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["results"][0]["key"] == "user3"

        # Search with complex query (combining operators and exact matches)
        result = await provider.execute(
            {"task": "search", "query": {"score": {"$gt": 85}, "active": True}}
        )
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["results"][0]["key"] == "user1"


@pytest.mark.asyncio
async def test_metadata_search_error_handling():
    """Test error handling in metadata search."""
    provider = MemoryCacheProvider()

    async with provider:
        # Test with missing query
        result = await provider.execute({"task": "search"})
        assert result["status"] == "error"
        assert "query is required" in result["message"].lower()

        # Test with invalid query format
        result = await provider.execute({"task": "search", "query": "not-a-dict"})
        assert result["status"] == "error"
        assert "query" in result["message"].lower()

        # Test search with no results
        result = await provider.execute(
            {"task": "search", "query": {"nonexistent": "field"}}
        )
        assert result["status"] == "success"
        assert result["count"] == 0
        assert len(result["results"]) == 0

        # Test with invalid operator
        result = await provider.execute(
            {"task": "search", "query": {"field": {"$invalid": "value"}}}
        )
        assert result["status"] == "success"
        assert result["count"] == 0


@pytest.mark.asyncio
async def test_memory_cache_tags():
    """Test tag functionality of memory cache provider."""
    provider = MemoryCacheProvider()

    async with provider:
        await provider.initialize()
        # Set values with tags
        await provider.execute(
            {"task": "set", "key": "tag1-key1", "value": "value1", "tags": ["tag1"]}
        )
        await provider.execute(
            {
                "task": "set",
                "key": "tag1-key2",
                "value": "value2",
                "tags": ["tag1", "tag2"],
            }
        )
        await provider.execute(
            {"task": "set", "key": "tag2-key", "value": "value3", "tags": ["tag2"]}
        )

        # Invalidate tag1
        result = await provider.execute({"task": "invalidate_tag", "tag": "tag1"})
        assert result["status"] == "success"
        assert result["message"] == "Tag invalidated"

        # Check keys are invalidated
        result = await provider.execute({"task": "get", "key": "tag1-key1"})
        assert result["status"] == "success"
        assert result["found"] is False

        result = await provider.execute({"task": "get", "key": "tag1-key2"})
        assert result["status"] == "success"
        assert result["found"] is False

        # But tag2-only key should still be there
        result = await provider.execute({"task": "get", "key": "tag2-key"})
        assert result["status"] == "success"
        assert result["found"] is True
        assert result["value"] == "value3"


@pytest.mark.asyncio
async def test_memory_cache_clear():
    """Test clear functionality of memory cache provider."""
    provider = MemoryCacheProvider()

    async with provider:
        await provider.initialize()
        # Set multiple values
        await provider.execute({"task": "set", "key": "key1", "value": "value1"})
        await provider.execute({"task": "set", "key": "key2", "value": "value2"})

        # Clear the cache
        result = await provider.execute({"task": "clear"})
        assert result["status"] == "success"
        assert result["message"] == "Cache cleared"

        # Verify keys are gone
        result = await provider.execute({"task": "get", "key": "key1"})
        assert result["status"] == "success"
        assert result["found"] is False

        result = await provider.execute({"task": "get", "key": "key2"})
        assert result["status"] == "success"
        assert result["found"] is False


@pytest.mark.asyncio
async def test_invalid_task():
    """Test handling of invalid task."""
    provider = MemoryCacheProvider()

    async with provider:
        await provider.initialize()
        result = await provider.execute({"task": "invalid_task"})
        assert result["status"] == "error"
        assert "unknown task" in result["message"].lower()


@pytest.mark.asyncio
async def test_config_validation():
    """Test configuration validation."""
    # Test invalid max_entries
    with pytest.raises(CacheError, match="max_entries must be greater than 0"):
        provider = MemoryCacheProvider(max_entries=0)
        await provider.initialize()

    # Test invalid default_ttl
    with pytest.raises(CacheError, match="default_ttl cannot be negative"):
        provider = MemoryCacheProvider(default_ttl=-1)
        await provider.initialize()


@pytest.mark.asyncio
async def test_input_validation():
    """Test input data validation."""
    provider = MemoryCacheProvider()

    async with provider:
        # Test negative TTL
        result = await provider.execute(
            {"task": "set", "key": "key", "value": "value", "ttl": -10}
        )
        assert result["status"] == "error"
        assert "ttl cannot be negative" in result["message"].lower()

        # Test invalid tags
        result = await provider.execute(
            {"task": "set", "key": "key", "value": "value", "tags": "not-a-list-or-set"}
        )
        assert result["status"] == "error"
        assert "tags must be a list or set" in result["message"].lower()


@pytest.mark.asyncio
async def test_context_manager():
    """Test the context manager functionality."""
    # Testing that __aenter__ initializes the provider
    provider = MemoryCacheProvider()
    assert getattr(provider, "initialized", False) is False

    async with provider as ctx:
        # Check that we get the same instance back
        assert ctx is provider
        assert provider.initialized is True

        # Set and get a value to ensure it works
        await provider.execute({"task": "set", "key": "cm-key", "value": "cm-value"})
        result = await provider.execute({"task": "get", "key": "cm-key"})
        assert result["status"] == "success"
        assert result["value"] == "cm-value"

    # Check that cleanup happened
    assert provider.initialized is False


@pytest.mark.asyncio
async def test_repr():
    """Test the __repr__ method."""
    provider = MemoryCacheProvider(max_entries=1000, default_ttl=300)

    # Test before initialization
    repr_str = repr(provider)
    assert "MemoryCacheProvider" in repr_str
    assert "initialized=False" in repr_str
    assert "max_entries=1000" in repr_str
    assert "default_ttl=300" in repr_str

    # Test after initialization
    async with provider:
        # Add some entries
        await provider.execute({"task": "set", "key": "key1", "value": "value1"})
        await provider.execute({"task": "set", "key": "key2", "value": "value2"})

        repr_str = repr(provider)
        assert "initialized=True" in repr_str
        assert "current_entries=2" in repr_str


@pytest.mark.asyncio
async def test_direct_adapter():
    """Test direct adapter pattern for memory cache provider."""
    from plugins.cache.memory.provider import MemoryCacheProvider

    adapter = MemoryCacheProvider(max_entries=100, default_ttl=60)
    await adapter.initialize()

    try:
        # Set a value
        result = await adapter.execute(
            {"task": "set", "key": "direct-key", "value": "direct-value"}
        )
        assert result["status"] == "success"
        assert result["message"] == "Value cached"

        # Get the value
        result = await adapter.execute({"task": "get", "key": "direct-key"})
        assert result["status"] == "success"
        assert result["value"] == "direct-value"
        assert result["found"] is True

    finally:
        await adapter.cleanup()
