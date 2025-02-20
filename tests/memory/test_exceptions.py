"""Tests for memory exceptions."""

import pytest

from pepperpy.core.errors import (
    MemoryBackendAlreadyExistsError,
    MemoryBackendError,
    MemoryBackendInvalidError,
    MemoryBackendNotFoundError,
    MemoryCleanupError,
    MemoryDeletionError,
    MemoryExistsError,
    MemoryRetrievalError,
    MemoryStorageError,
    PepperpyMemoryError,
)


def test_memory_error_hierarchy():
    """Test memory error class hierarchy."""
    # Test base exception
    assert issubclass(PepperpyMemoryError, Exception)

    # Test backend error hierarchy
    assert issubclass(MemoryBackendError, PepperpyMemoryError)
    assert issubclass(MemoryStorageError, MemoryBackendError)
    assert issubclass(MemoryRetrievalError, MemoryBackendError)
    assert issubclass(MemoryDeletionError, MemoryBackendError)
    assert issubclass(MemoryExistsError, MemoryBackendError)
    assert issubclass(MemoryCleanupError, MemoryBackendError)

    # Test other memory errors
    assert issubclass(MemoryBackendNotFoundError, PepperpyMemoryError)
    assert issubclass(MemoryBackendAlreadyExistsError, PepperpyMemoryError)
    assert issubclass(MemoryBackendInvalidError, PepperpyMemoryError)


def test_memory_error_messages():
    """Test memory error messages."""
    # Test base exception
    error = PepperpyMemoryError("Test error")
    assert str(error) == "Test error"

    # Test backend errors
    error = MemoryBackendError("Backend error")
    assert str(error) == "Backend error"

    error = MemoryStorageError("Storage error")
    assert str(error) == "Storage error"

    error = MemoryRetrievalError("Retrieval error")
    assert str(error) == "Retrieval error"

    error = MemoryDeletionError("Deletion error")
    assert str(error) == "Deletion error"

    error = MemoryExistsError("Exists error")
    assert str(error) == "Exists error"

    error = MemoryCleanupError("Cleanup error")
    assert str(error) == "Cleanup error"

    # Test other memory errors
    error = MemoryBackendNotFoundError("Backend not found")
    assert str(error) == "Backend not found"

    error = MemoryBackendAlreadyExistsError("Backend already exists")
    assert str(error) == "Backend already exists"

    error = MemoryBackendInvalidError("Invalid backend")
    assert str(error) == "Invalid backend"


def test_memory_error_raising():
    """Test raising memory errors."""
    # Test base exception
    with pytest.raises(PepperpyMemoryError, match="Test error"):
        raise PepperpyMemoryError("Test error")

    # Test backend errors
    with pytest.raises(MemoryBackendError, match="Backend error"):
        raise MemoryBackendError("Backend error")

    with pytest.raises(MemoryStorageError, match="Storage error"):
        raise MemoryStorageError("Storage error")

    with pytest.raises(MemoryRetrievalError, match="Retrieval error"):
        raise MemoryRetrievalError("Retrieval error")

    with pytest.raises(MemoryDeletionError, match="Deletion error"):
        raise MemoryDeletionError("Deletion error")

    with pytest.raises(MemoryExistsError, match="Exists error"):
        raise MemoryExistsError("Exists error")

    with pytest.raises(MemoryCleanupError, match="Cleanup error"):
        raise MemoryCleanupError("Cleanup error")

    # Test other memory errors
    with pytest.raises(MemoryBackendNotFoundError, match="Backend not found"):
        raise MemoryBackendNotFoundError("Backend not found")

    with pytest.raises(MemoryBackendAlreadyExistsError, match="Backend already exists"):
        raise MemoryBackendAlreadyExistsError("Backend already exists")

    with pytest.raises(MemoryBackendInvalidError, match="Invalid backend"):
        raise MemoryBackendInvalidError("Invalid backend")
