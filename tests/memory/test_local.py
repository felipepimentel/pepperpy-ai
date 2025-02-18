"""Tests for local memory provider."""

import asyncio
import json
import pickle
from typing import AsyncGenerator

import pytest

from pepperpy.memory.base import MemoryItem
from pepperpy.memory.providers.local import LocalProvider


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory."""
    return tmp_path


@pytest.fixture
async def provider(temp_dir) -> AsyncGenerator[LocalProvider, None]:
    """Create test provider."""
    provider = LocalProvider(path=temp_dir, format="json")
    yield provider


@pytest.mark.asyncio
async def test_set_get_basic(provider):
    """Test basic set and get operations."""
    # Set value
    await provider.set("test_key", "test_value")

    # Get value
    value = await provider.get("test_key")
    assert value == "test_value"


@pytest.mark.asyncio
async def test_get_nonexistent(provider):
    """Test getting nonexistent key."""
    # Get with default
    value = await provider.get("nonexistent", default="default")
    assert value == "default"

    # Get without default
    value = await provider.get("nonexistent")
    assert value is None


@pytest.mark.asyncio
async def test_set_get_with_metadata(provider):
    """Test set and get with metadata."""
    # Set with metadata
    metadata = {"type": "test", "tags": ["a", "b"]}
    await provider.set("test_key", "test_value", metadata=metadata)

    # Get value
    value = await provider.get("test_key")
    assert value == "test_value"

    # Verify metadata in file
    path = provider._get_path("test_key")
    with open(path) as f:
        data = json.load(f)
        assert data["metadata"] == metadata


@pytest.mark.asyncio
async def test_set_get_with_ttl(provider):
    """Test set and get with TTL."""
    # Set with short TTL
    await provider.set("test_key", "test_value", ttl=0.1)

    # Get immediately
    value = await provider.get("test_key")
    assert value == "test_value"

    # Wait for TTL
    await asyncio.sleep(0.2)

    # Get after TTL
    value = await provider.get("test_key")
    assert value is None


@pytest.mark.asyncio
async def test_delete(provider):
    """Test key deletion."""
    # Set value
    await provider.set("test_key", "test_value")

    # Delete key
    result = await provider.delete("test_key")
    assert result is True

    # Verify deletion
    value = await provider.get("test_key")
    assert value is None

    # Delete nonexistent key
    result = await provider.delete("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_search(provider):
    """Test key search."""
    # Set test values
    await provider.set("test_1", "value_1")
    await provider.set("test_2", "value_2")
    await provider.set("other", "value_3")

    # Search with pattern
    keys = await provider.search("test_*")
    assert len(keys) == 2
    assert "test_1" in keys
    assert "test_2" in keys

    # Search with limit
    keys = await provider.search("test_*", limit=1)
    assert len(keys) == 1


@pytest.mark.asyncio
async def test_clear(provider):
    """Test memory clearing."""
    # Set test values
    await provider.set("test_1", "value_1")
    await provider.set("test_2", "value_2")

    # Clear memory
    await provider.clear()

    # Verify clearing
    value1 = await provider.get("test_1")
    value2 = await provider.get("test_2")
    assert value1 is None
    assert value2 is None


@pytest.mark.asyncio
async def test_pickle_format(temp_dir):
    """Test pickle storage format."""
    # Create provider with pickle format
    provider = LocalProvider(path=temp_dir, format="pickle")

    # Set complex value
    complex_value = {"data": [1, 2, 3], "nested": {"a": 1, "b": 2}}
    await provider.set("test_key", complex_value)

    # Get value
    value = await provider.get("test_key")
    assert value == complex_value

    # Verify pickle format
    path = provider._get_path("test_key")
    with open(path, "rb") as f:
        data = pickle.load(f)
        assert isinstance(data, MemoryItem)
        assert data.value == complex_value


@pytest.mark.asyncio
async def test_key_sanitization(provider):
    """Test key name sanitization."""
    # Set value with special characters
    key = "test/key with spaces!@#"
    await provider.set(key, "test_value")

    # Get value
    value = await provider.get(key)
    assert value == "test_value"

    # Verify sanitized filename
    path = provider._get_path(key)
    assert "/" not in path.name
    assert " " not in path.name
    assert "!" not in path.name
    assert "@" not in path.name
    assert "#" not in path.name
