"""Tests for the unified import system."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.core.imports.unified import (
    ImportError,
    ImportManager,
    ImportMetadata,
    ImportProfiler,
    ImportType,
    ImportValidator,
    get_import_manager,
)


def test_import_types():
    """Test import type enumeration."""
    assert ImportType.DIRECT.name == "DIRECT"
    assert ImportType.LAZY.name == "LAZY"
    assert ImportType.CONDITIONAL.name == "CONDITIONAL"


def test_import_metadata():
    """Test import metadata creation and properties."""
    metadata = ImportMetadata(
        name="test_module",
        path=Path("/test/module.py"),
        type=ImportType.DIRECT,
    )
    assert metadata.name == "test_module"
    assert metadata.path == Path("/test/module.py")
    assert metadata.type == ImportType.DIRECT
    assert metadata.dependencies == set()
    assert metadata.import_time == 0.0
    assert metadata.size == 0
    assert not metadata.is_package


class TestImportValidator:
    """Test cases for ImportValidator."""

    def test_validate_module_structure(self):
        """Test module structure validation."""
        validator = ImportValidator()

        # Test with valid module
        assert validator.validate_module_structure("os")

        # Test with invalid module
        assert not validator.validate_module_structure("nonexistent_module")

    def test_check_circular_imports(self):
        """Test circular import detection."""
        validator = ImportValidator()

        # Test with non-circular imports
        assert not validator.check_circular_imports("os")

        # Test with circular imports (mock)
        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_module.__name__ = "circular_module"
            mock_import.return_value = mock_module

            circular_deps = validator.check_circular_imports("circular_module")
            assert "circular_module" in circular_deps


class TestImportProfiler:
    """Test cases for ImportProfiler."""

    def test_import_timing(self):
        """Test import timing functionality."""
        profiler = ImportProfiler()

        # Test start_import
        start_time = profiler.start_import("test_module")
        assert isinstance(start_time, float)

        # Test end_import
        profiler.end_import("test_module", start_time)
        assert "test_module" in profiler.import_times
        assert "test_module" in profiler.import_counts
        assert profiler.import_counts["test_module"] == 1


class TestImportManager:
    """Test cases for ImportManager."""

    def test_singleton(self):
        """Test singleton pattern."""
        manager1 = ImportManager()
        manager2 = ImportManager()
        assert manager1 is manager2

    def test_register_module(self):
        """Test module registration."""
        manager = ImportManager()

        # Test with valid module
        metadata = manager.register_module("os")
        assert metadata.name == "os"
        assert metadata.path is not None
        assert metadata.type == ImportType.DIRECT

        # Test with invalid module
        with pytest.raises(ImportError):
            manager.register_module("nonexistent_module")

    def test_lazy_import(self):
        """Test lazy import functionality."""
        manager = ImportManager()

        # Test lazy import
        module = manager.lazy_import("os")
        assert module is not None
        assert manager.modules["os"].type == ImportType.LAZY

    def test_get_dependencies(self):
        """Test dependency retrieval."""
        manager = ImportManager()

        # Test with registered module
        deps = manager.get_dependencies("os")
        assert isinstance(deps, set)

        # Test with unregistered module
        deps = manager.get_dependencies("sys")
        assert isinstance(deps, set)

    def test_check_circular_imports(self):
        """Test circular import checking."""
        manager = ImportManager()

        # Test with non-circular imports
        circulars = manager.check_circular_imports("os")
        assert not circulars

    def test_validate_imports(self):
        """Test import validation."""
        manager = ImportManager()

        # Test with valid module
        assert manager.validate_imports("os")

        # Test with invalid module
        assert not manager.validate_imports("nonexistent_module")

    def test_get_import_stats(self):
        """Test import statistics retrieval."""
        manager = ImportManager()

        # Test with unregistered module
        stats = manager.get_import_stats("unregistered_module")
        assert not stats

        # Test with registered module
        manager.register_module("os")
        stats = manager.get_import_stats("os")
        assert "import_time" in stats
        assert "size" in stats
        assert "import_count" in stats


def test_get_import_manager():
    """Test global import manager retrieval."""
    manager = get_import_manager()
    assert isinstance(manager, ImportManager)
    assert manager is ImportManager()
