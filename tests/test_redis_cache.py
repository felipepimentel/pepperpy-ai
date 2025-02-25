"""Tests for the Redis cache store."""

import asyncio
import os
import time
from typing import AsyncGenerator

import pytest
import redis.asyncio as redis

from pepperpy.caching.errors import CacheBackendError, CacheKeyError
from pepperpy.caching.policies.lru import LRUPolicy
from pepperpy.caching.stores.redis import RedisStore


@pytest.fixture
def redis_url() -> str:
    """Get Redis URL from environment or use default."""
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
async def redis_client(redis_url: str) -> AsyncGenerator[redis.Redis[bytes], None]:
    """Create a Redis client for testing."""
    client = redis.from_url(redis_url)
    try:
        await client.ping()
    except redis.ConnectionError as e:
        pytest.skip(f"Redis not available: {e}")
        
    yield client
    await client.close()


@pytest.fixture
async def redis_store(redis_url: str) -> AsyncGenerator[RedisStore[str], None]:
    """Create a Redis store for testing."""
    store = RedisStore[str](redis_url, prefix="test:")
    yield store
    await store.clear()


@pytest.mark.asyncio
async def test_redis_store_basic_operations(redis_store: RedisStore[str]) -> None:
    """Test basic Redis store operations."""
    # Test set and get
    assert await redis_store.set("key1", "value1")
    assert await redis_store.get("key1") == "value1"
    
    # Test default value
    assert await redis_store.get("nonexistent", "default") == "default"
    
    # Test delete
    assert await redis_store.delete("key1")
    assert await redis_store.get("key1") is None
    
    # Test clear
    assert await redis_store.set("key2", "value2")
    assert await redis_store.clear()
    assert await redis_store.get("key2") is None


@pytest.mark.asyncio
async def test_redis_store_with_ttl(redis_store: RedisStore[str]) -> None:
    """Test Redis store TTL functionality."""
    # Set with TTL
    assert await redis_store.set("key1", "value1", ttl=1)
    assert await redis_store.get("key1") == "value1"
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    assert await redis_store.get("key1") is None


@pytest.mark.asyncio
async def test_redis_store_with_metadata(redis_store: RedisStore[str]) -> None:
    """Test Redis store metadata functionality."""
    metadata = {"version": 1, "author": "test"}
    
    # Set with metadata
    assert await redis_store.set("key1", "value1", metadata=metadata)
    assert await redis_store.get_metadata("key1") == metadata
    
    # Update metadata
    new_metadata = {"version": 2, "author": "test"}
    assert await redis_store.update_metadata("key1", new_metadata)
    assert await redis_store.get_metadata("key1") == new_metadata


@pytest.mark.asyncio
async def test_redis_store_with_lru_policy(redis_store: RedisStore[str]) -> None:
    """Test Redis store with LRU policy."""
    policy = LRUPolicy[str](max_size=2)
    redis_store.policy = policy
    
    # Fill cache to capacity
    assert await redis_store.set("key1", "value1")
    assert await redis_store.set("key2", "value2")
    
    # Try to add another item (should evict oldest)
    assert await redis_store.set("key3", "value3")
    assert await redis_store.get("key1") is None  # Evicted
    assert await redis_store.get("key2") == "value2"
    assert await redis_store.get("key3") == "value3"


@pytest.mark.asyncio
async def test_redis_store_error_handling(redis_store: RedisStore[str]) -> None:
    """Test Redis store error handling."""
    # Test invalid key type
    with pytest.raises(CacheKeyError):
        await redis_store.get(123)  # type: ignore
        
    with pytest.raises(CacheKeyError):
        await redis_store.set(123, "value")  # type: ignore
        
    with pytest.raises(CacheKeyError):
        await redis_store.delete(123)  # type: ignore
        
    # Test connection error
    store = RedisStore[str]("redis://nonexistent:6379/0")
    with pytest.raises(CacheBackendError):
        await store.get("key") 