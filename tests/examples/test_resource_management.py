"""Tests for resource management example."""

from datetime import UTC, datetime, timedelta

import pytest

from examples.resource_management import (
    basic_memory_example,
    expiration_example,
    session_example,
)
from pepperpy.memory.errors import MemoryKeyError


@pytest.mark.asyncio
async def test_basic_memory_example(capsys):
    """Test basic memory example."""
    await basic_memory_example()
    captured = capsys.readouterr()

    # Check output
    assert "User ID: 12345" in captured.out
    assert "Session Token: abc123" in captured.out


@pytest.mark.asyncio
async def test_session_example(capsys):
    """Test resource session example."""
    await session_example()
    captured = capsys.readouterr()

    # Check output
    assert "Processing data: {'status': 'processing'}" in captured.out


@pytest.mark.asyncio
async def test_expiration_example(capsys):
    """Test expiration example."""
    await expiration_example()
    captured = capsys.readouterr()

    # Check output
    assert "Waiting for value to expire..." in captured.out
    assert "Value has expired and was cleaned up" in captured.out


@pytest.mark.asyncio
async def test_example_error_handling():
    """Test error handling in examples."""
    from pepperpy.memory.simple import SimpleMemory

    # Test uninitialized memory
    memory = SimpleMemory()
    with pytest.raises(MemoryError):
        await memory.store("key", "value")

    # Test expired value
    memory = SimpleMemory()
    await memory.initialize()

    # Store value that expires immediately
    await memory.store(
        "expired",
        "value",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    # Try to retrieve expired value
    with pytest.raises(MemoryKeyError):
        await memory.retrieve("expired")

    await memory.cleanup()
