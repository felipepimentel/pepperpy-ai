"""Tests for the unified import system.

This module tests the core functionality of the import system including:
- Import manager
- Import cache
- Import validation
- Import profiling
"""

import os
import sys
import time
from pathlib import Path
from typing import Generator

import pytest

from pepperpy.core.imports.unified import (
    CacheEntry,
    CircularImportError,
    ImportCache,
    ImportError,
    ImportManager,
    ImportMetadata,
    ImportProfiler,
    ImportType,
    ImportValidationError,
    ImportValidator,
    get_import_manager,
)


@pytest.fixture
def import_manager() -> ImportManager:
    """Create a fresh ImportManager instance for testing."""
    manager = ImportManager()
    yield manager


@pytest.fixture
def import_cache() -> ImportCache:
    """Create a fresh ImportCache instance for testing."""
    cache = ImportCache(
        max_size=1024 * 1024,  # 1MB
        max_entries=10,
        ttl=60,  # 1 minute
    )
    yield cache


@pytest.fixture
def import_profiler() -> ImportProfiler:
    """Create a fresh ImportProfiler instance for testing."""
    profiler = ImportProfiler()
    yield profiler


@pytest.fixture
def import_validator() -> ImportValidator:
    """Create a fresh ImportValidator instance for testing."""
    validator = ImportValidator()
    yield validator


def test_import_manager_singleton():
    """Test that ImportManager is a singleton."""
    manager1 = get_import_manager()
    manager2 = get_import_manager()
    assert manager1 is manager2


def test_import_manager_registration(import_manager: ImportManager):
    """Test module registration."""
    metadata = import_manager.register_module("sys")
    assert metadata.name == "sys"
    assert metadata.error_count == 0
    assert metadata.type == ImportType.DIRECT


def test_import_manager_lazy_import(import_manager: ImportManager):
    """Test lazy module import."""
    module = import_manager.lazy_import("sys")
    assert module.__name__ == "sys"


def test_import_cache_operations(import_cache: ImportCache):
    """Test cache operations."""
    # Set up test data
    metadata = ImportMetadata(name="sys")
    import_cache.set("sys", sys.modules["sys"], metadata)

    # Test cache hit
    cached = import_cache.get("sys")
    assert cached == sys.modules["sys"]
    assert import_cache._hits == 1

    # Test cache miss
    missing = import_cache.get("nonexistent")
    assert missing is None
    assert import_cache._misses == 1


def test_import_cache_cleanup(import_cache: ImportCache):
    """Test cache cleanup."""
    # Fill cache
    for i in range(20):  # More than max_entries
        metadata = ImportMetadata(name=f"module{i}")
        import_cache.set(f"module{i}", sys.modules["sys"], metadata)

    # Check that cache size is limited
    assert len(import_cache._cache) <= import_cache._max_entries


def test_import_profiler_timing(import_profiler: ImportProfiler):
    """Test import profiling."""
    start_time = import_profiler.start_import("sys")
    time.sleep(0.1)  # Simulate import time
    import_profiler.end_import("sys", start_time)

    assert "sys" in import_profiler.import_times
    assert import_profiler.import_times["sys"] >= 0.1


def test_import_validator_structure(import_validator: ImportValidator):
    """Test module structure validation."""
    assert import_validator.validate_module_structure("sys")
    assert not import_validator.validate_module_structure("nonexistent_module")


def test_circular_import_detection(import_validator: ImportValidator):
    """Test circular import detection."""
    # Create temporary modules for testing
    sys.modules["test_a"] = type("ModuleA", (), {"__name__": "test_a"})
    sys.modules["test_b"] = type("ModuleB", (), {"__name__": "test_b"})

    try:
        # No circular imports
        chain = import_validator.check_circular_imports("sys")
        assert not chain

    finally:
        # Clean up
        del sys.modules["test_a"]
        del sys.modules["test_b"]


def test_import_metadata():
    """Test import metadata."""
    metadata = ImportMetadata(
        name="test_module",
        path=Path("/path/to/module.py"),
        type=ImportType.LAZY,
    )

    assert metadata.name == "test_module"
    assert metadata.path == Path("/path/to/module.py")
    assert metadata.type == ImportType.LAZY
    assert metadata.error_count == 0


def test_cache_entry():
    """Test cache entry."""
    metadata = ImportMetadata(name="sys")
    entry = CacheEntry(module=sys.modules["sys"], metadata=metadata)

    assert entry.module == sys.modules["sys"]
    assert entry.metadata == metadata
    assert entry.last_accessed > 0


def test_import_types():
    """Test import types."""
    assert ImportType.DIRECT.name == "DIRECT"
    assert ImportType.LAZY.name == "LAZY"
    assert ImportType.CONDITIONAL.name == "CONDITIONAL"


def test_import_errors():
    """Test import errors."""
    with pytest.raises(ImportError):
        raise ImportError("Test error")

    with pytest.raises(CircularImportError):
        raise CircularImportError("test_module", ["a", "b", "a"])

    with pytest.raises(ImportValidationError):
        raise ImportValidationError("Test validation error")