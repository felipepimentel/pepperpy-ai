"""Tests for import optimization system."""

import sys
import time
from collections.abc import Generator
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.core.imports import ImportSystem
from pepperpy.utils.imports_cache import ImportCache
from pepperpy.utils.imports_hook import (
    ImportOptimizer,
)
from pepperpy.utils.imports_profiler import ImportProfiler
from pepperpy.utils.modules import ModuleManager


@pytest.fixture
def module_manager() -> ModuleManager:
    """Create module manager fixture."""
    return ModuleManager()


@pytest.fixture
def import_cache() -> ImportCache:
    """Create import cache fixture."""
    return ImportCache(
        max_size=1024 * 1024,  # 1MB
        max_entries=100,
        ttl=60.0,  # 1 minute
    )


@pytest.fixture
def import_profiler() -> ImportProfiler:
    """Create import profiler fixture."""
    return ImportProfiler()


@pytest.fixture
def import_optimizer(module_manager: ModuleManager) -> ImportOptimizer:
    """Create import optimizer fixture."""
    return ImportOptimizer(
        module_manager,
        max_cache_size=1024 * 1024,  # 1MB
        max_cache_entries=100,
        cache_ttl=60.0,  # 1 minute
        max_retries=3,
    )


@pytest.fixture
def import_system() -> ImportSystem:
    """Create import system fixture."""
    return ImportSystem(
        max_cache_size=1024 * 1024,  # 1MB
        max_cache_entries=100,
        cache_ttl=3600,  # 1 hour
        max_retries=3,
    )


@pytest.fixture
def temp_module(tmp_path: Path) -> Generator[tuple[str, str], None, None]:
    """Create temporary module fixture.

    Yields:
        Tuple containing module name and path
    """
    module_name = "test_module"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text("x = 1")

    sys.path.insert(0, str(tmp_path))
    try:
        yield module_name, str(module_path)
    finally:
        sys.path.pop(0)


@pytest.fixture
def temp_modules(tmp_path: Path) -> Generator[list[tuple[str, str]], None, None]:
    """Create multiple temporary module fixtures.

    Yields:
        List of tuples containing module names and paths
    """
    modules = []
    for i in range(3):
        name = f"test_module_{i}"
        path = tmp_path / f"{name}.py"
        if i == 0:
            path.write_text("from test_module_1 import y\nx = 1")
        elif i == 1:
            path.write_text("from test_module_2 import z\ny = 2")
        else:
            path.write_text("z = 3")
        modules.append((name, str(path)))

    sys.path.insert(0, str(tmp_path))
    try:
        yield modules
    finally:
        sys.path.pop(0)


def test_import_cache_get_set(import_cache: ImportCache) -> None:
    """Test import cache get and set."""
    # Create test module
    module = ModuleType("test_module")
    module.__file__ = __file__
    module.__spec__ = None

    # Set module in cache
    import_cache.set("test_module", module)

    # Get module from cache
    cached_module = import_cache.get("test_module")
    assert cached_module is module

    # Get cache stats
    stats = import_cache.get_cache_stats()
    assert stats["total_entries"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 0


def test_import_cache_dependencies(import_cache: ImportCache) -> None:
    """Test import cache dependencies."""
    # Create test modules
    module_a = ModuleType("module_a")
    module_a.__file__ = __file__
    module_a.__spec__ = None

    module_b = ModuleType("module_b")
    module_b.__file__ = __file__
    module_b.__spec__ = None

    # Set modules in cache with dependencies
    import_cache.set("module_a", module_a)
    import_cache.set("module_b", module_b, {"module_a"})

    # Get dependent modules
    dependents = import_cache.get_dependent_modules(__file__)
    assert "module_a" in dependents
    assert "module_b" in dependents

    # Invalidate module_a
    import_cache.invalidate("module_a")

    # Check that module_b was also invalidated
    assert import_cache.get("module_b") is None


def test_import_profiler(import_profiler: ImportProfiler) -> None:
    """Test import profiler."""
    # Start profiling
    import_profiler.start_import("test_module")

    # Simulate import
    time.sleep(0.1)

    # Finish profiling
    profile = import_profiler.finish_import("test_module", {"dep1", "dep2"})

    # Check profile
    assert profile.module == "test_module"
    assert profile.duration >= 0.1
    assert profile.memory_delta >= 0
    assert profile.dependencies == {"dep1", "dep2"}
    assert not profile.errors

    # Get slow imports
    slow_imports = import_profiler.get_slow_imports(threshold=0.05)
    assert len(slow_imports) == 1
    assert slow_imports[0].module == "test_module"

    # Get memory intensive imports
    memory_imports = import_profiler.get_memory_intensive_imports(threshold=0)
    assert len(memory_imports) == 1
    assert memory_imports[0].module == "test_module"

    # Analyze imports
    analysis = import_profiler.analyze_imports()
    assert analysis["total_imports"] == 1
    assert analysis["total_duration"] >= 0.1
    assert analysis["error_count"] == 0


def test_import_optimizer(import_optimizer: ImportOptimizer) -> None:
    """Test import optimizer."""
    # Create test module
    module = ModuleType("test_module")
    module.__file__ = __file__
    module.__spec__ = None

    # Set module in optimizer
    import_optimizer.set("test_module", module)

    # Get module from optimizer
    cached_module = import_optimizer.get("test_module")
    assert cached_module is module

    # Get import profiles
    profiles = import_optimizer.get_import_profiles()
    assert "profiles" in profiles
    assert "analysis" in profiles
    assert "dependency_graph" in profiles
    assert "error_counts" in profiles

    # Get cache stats
    stats = import_optimizer.get_cache_stats()
    assert stats["total_entries"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 0


def test_import_cache_constraints(import_cache: ImportCache) -> None:
    """Test import cache constraints."""
    # Create test modules
    modules = []
    for i in range(150):
        module = ModuleType(f"module_{i}")
        module.__file__ = __file__
        module.__spec__ = None
        modules.append(module)

    # Set modules in cache
    for module in modules:
        import_cache.set(module.__name__, module)

    # Check that cache size is limited
    assert len(import_cache._cache) <= 100

    # Check TTL expiration
    time.sleep(0.1)
    import_cache._ttl = 0.05  # Set TTL to 50ms
    import_cache._evict_entries()
    assert len(import_cache._cache) < 100


def test_import_profiler_memory_tracking(import_profiler: ImportProfiler) -> None:
    """Test import profiler memory tracking."""
    # Start profiling
    import_profiler.start_import("test_module")

    # Allocate some memory
    data = [0] * 1000000  # Allocate ~8MB

    # Finish profiling
    profile = import_profiler.finish_import("test_module")

    # Check memory impact
    assert profile.memory_delta > 0
    assert profile.memory_after > profile.memory_before

    # Get memory intensive imports
    memory_imports = import_profiler.get_memory_intensive_imports(threshold=0)
    assert len(memory_imports) == 1
    assert memory_imports[0].module == "test_module"
    assert memory_imports[0].memory_delta > 0

    # Cleanup
    del data


def test_import_optimizer_error_handling(import_optimizer: ImportOptimizer) -> None:
    """Test import optimizer error handling."""
    # Try to import non-existent module
    with pytest.raises(ImportError) as exc_info:
        import_optimizer.exec_module(ModuleType("non_existent"))

    assert "Failed to import" in str(exc_info.value)

    # Check error counts
    profiles = import_optimizer.get_import_profiles()
    assert profiles["error_counts"]["non_existent"] >= 1


def test_import_cache_metadata(import_cache: ImportCache) -> None:
    """Test import cache metadata."""
    # Create test module
    module = ModuleType("test_module")
    module.__file__ = __file__
    module.__spec__ = None

    # Set module in cache with metadata
    metadata = {
        "version": "1.0.0",
        "author": "test",
        "tags": ["test", "example"],
    }
    import_cache.set("test_module", module, metadata=metadata)

    # Get module from cache
    entry = import_cache._cache.get("test_module")
    assert entry is not None
    assert entry.metadata == metadata


def test_import_system(
    import_system: ImportSystem, temp_modules: list[tuple[str, str]]
) -> None:
    """Test import system."""
    # Test lazy imports
    with patch("pepperpy.utils.imports.lazy_import") as mock_lazy_import:
        mock_module = MagicMock()
        mock_lazy_import.return_value = mock_module
        lazy_mod = import_system.lazy_import(temp_modules[0][0])
        assert lazy_mod == mock_module

    # Test safe imports
    with patch("pepperpy.utils.imports.safe_import") as mock_safe_import:
        mock_module = MagicMock()
        mock_safe_import.return_value = mock_module
        for name, _ in temp_modules:
            module = import_system.safe_import(name)
            assert module == mock_module

    # Test dependency tracking
    deps = import_system.get_dependencies(temp_modules[0][0])
    assert isinstance(deps, set)

    rev_deps = import_system.get_reverse_dependencies(temp_modules[-1][0])
    assert isinstance(rev_deps, set)

    # Test dependency order
    order = import_system.get_dependency_order([m[0] for m in temp_modules])
    assert len(order) >= len(temp_modules)

    # Test circular import detection
    circles = import_system.check_circular_imports(temp_modules[0][0])
    assert isinstance(circles, list)

    # Test import analysis
    profiles = import_system.get_import_profiles()
    assert "profiles" in profiles
    assert "analysis" in profiles
    assert "dependency_graph" in profiles
    assert "error_counts" in profiles

    analysis = import_system.analyze_imports()
    assert "total_imports" in analysis
    assert "total_memory_impact" in analysis

    slow_imports = import_system.get_slow_imports(0.0)  # Get all imports
    assert isinstance(slow_imports, list)

    # Test module reloading
    with patch(
        "pepperpy.utils.imports_hook.ImportOptimizer.reload_module"
    ) as mock_reload:
        mock_module = MagicMock()
        mock_reload.return_value = mock_module
        reloaded = import_system.reload_module(temp_modules[0][0])
        assert reloaded == mock_module

    # Test cache invalidation
    import_system.invalidate_module(temp_modules[0][0])
    import_system.invalidate_path(temp_modules[0][1])
    import_system.clear_cache()
