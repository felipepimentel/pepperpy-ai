"""Tests for the caching system."""

import asyncio
import time
from typing import Any, Dict, Optional

import pytest

from pepperpy.caching.errors import CacheError, CacheKeyError
from pepperpy.caching.invalidation.strategy import TTLInvalidation
from pepperpy.caching.metrics.collector import CacheMetrics
from pepperpy.caching.policies.lru import LRUPolicy
from pepperpy.caching.stores.memory import MemoryStore
from pepperpy.caching.types import CacheKey, CacheMetadata


@pytest.fixture
def memory_store() -> MemoryStore[str]:
    """Create a memory store for testing."""
    return MemoryStore()


@pytest.fixture
def lru_policy() -> LRUPolicy[str]:
    """Create an LRU policy for testing."""
    return LRUPolicy(max_size=2)


@pytest.fixture
def metrics() -> CacheMetrics:
    """Create a metrics collector for testing."""
    return CacheMetrics()


@pytest.mark.asyncio
async def test_memory_store_basic_operations(memory_store: MemoryStore[str]) -> None:
    """Test basic memory store operations."""
    # Test set and get
    assert await memory_store.set("key1", "value1")
    assert await memory_store.get("key1") == "value1"
    
    # Test default value
    assert await memory_store.get("nonexistent", "default") == "default"
    
    # Test delete
    assert await memory_store.delete("key1")
    assert await memory_store.get("key1") is None
    
    # Test clear
    assert await memory_store.set("key2", "value2")
    assert await memory_store.clear()
    assert await memory_store.get("key2") is None


@pytest.mark.asyncio
async def test_memory_store_with_ttl(memory_store: MemoryStore[str]) -> None:
    """Test memory store TTL functionality."""
    # Set with TTL
    assert await memory_store.set("key1", "value1", ttl=1)
    assert await memory_store.get("key1") == "value1"
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    assert await memory_store.get("key1") is None


@pytest.mark.asyncio
async def test_memory_store_with_metadata(memory_store: MemoryStore[str]) -> None:
    """Test memory store metadata functionality."""
    metadata = {"version": 1, "author": "test"}
    
    # Set with metadata
    assert await memory_store.set("key1", "value1", metadata=metadata)
    assert await memory_store.get_metadata("key1") == metadata
    
    # Update metadata
    new_metadata = {"version": 2, "author": "test"}
    assert await memory_store.update_metadata("key1", new_metadata)
    assert await memory_store.get_metadata("key1") == new_metadata


@pytest.mark.asyncio
async def test_lru_policy(
    memory_store: MemoryStore[str],
    lru_policy: LRUPolicy[str],
) -> None:
    """Test LRU policy functionality."""
    memory_store.policy = lru_policy
    
    # Fill cache to capacity
    assert await memory_store.set("key1", "value1")
    assert await memory_store.set("key2", "value2")
    
    # Try to add another item (should evict oldest)
    assert await memory_store.set("key3", "value3")
    assert await memory_store.get("key1") is None  # Evicted
    assert await memory_store.get("key2") == "value2"
    assert await memory_store.get("key3") == "value3"


def test_metrics(metrics: CacheMetrics) -> None:
    """Test metrics collection."""
    # Track operations
    metrics.track_hit(latency=0.1)
    metrics.track_miss(latency=0.2)
    metrics.track_set(latency=0.3)
    metrics.track_eviction()
    
    # Check stats
    stats = metrics.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["sets"] == 1
    assert stats["evictions"] == 1
    assert stats["hit_ratio"] == 0.5
    assert 0.09 < stats["avg_get_latency"] < 0.16  # Average of hit and miss
    assert 0.29 < stats["avg_set_latency"] < 0.31


@pytest.mark.asyncio
async def test_ttl_invalidation() -> None:
    """Test TTL invalidation strategy."""
    strategy = TTLInvalidation()
    
    # Test with expired TTL
    metadata = {
        "ttl": 1,
        "created_at": time.time() - 2,  # 2 seconds ago
    }
    assert strategy.should_invalidate("key1", metadata)
    
    # Test with valid TTL
    metadata = {
        "ttl": 10,
        "created_at": time.time(),  # Just now
    }
    assert not strategy.should_invalidate("key1", metadata)
    
    # Test with missing metadata
    assert not strategy.should_invalidate("key1", None)


@pytest.mark.asyncio
async def test_error_handling(memory_store: MemoryStore[str]) -> None:
    """Test error handling."""
    # Test invalid key type
    with pytest.raises(CacheKeyError):
        await memory_store.get(123)  # type: ignore
        
    with pytest.raises(CacheKeyError):
        await memory_store.set(123, "value")  # type: ignore
        
    with pytest.raises(CacheKeyError):
        await memory_store.delete(123)  # type: ignore 