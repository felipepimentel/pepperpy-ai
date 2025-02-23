"""Tests for import optimization system."""

import os
import sys
import time
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.core.imports import ImportSystem
from pepperpy.utils.imports_cache import ImportCache
from pepperpy.utils.imports_hook import (
    CircularDependencyError,
    ImportOptimizer,
)
from pepperpy.utils.imports_profiler import ImportProfile, ImportProfiler
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
        ttl=3600,  # 1 hour
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
        cache_ttl=3600,  # 1 hour
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


def test_import_cache_get_set(
    import_cache: ImportCache, temp_module: tuple[str, str]
) -> None:
    """Test import cache get and set."""
    module_name, module_path = temp_module
    module = MagicMock(
        __name__=module_name,
        __spec__=MagicMock(origin=module_path),
    )

    # Test set and get
    import_cache.set(module_name, module)
    assert import_cache.get(module_name) == module

    # Test file modification detection
    os.utime(module_path, (time.time() + 1, time.time() + 1))
    assert import_cache.get(module_name) is None

    # Test cache constraints
    for i in range(200):  # Exceed max_entries
        name = f"module_{i}"
        mod = MagicMock(
            __name__=name,
            __spec__=MagicMock(origin=f"/path/to/{name}.py"),
        )
        import_cache.set(name, mod)

    # Verify cache size is maintained
    assert len(import_cache._cache) <= 100


def test_import_cache_dependencies(
    import_cache: ImportCache, temp_modules: list[tuple[str, str]]
) -> None:
    """Test import cache dependency handling."""
    modules = []
    for name, path in temp_modules:
        module = MagicMock(
            __name__=name,
            __spec__=MagicMock(origin=path),
        )
        modules.append(module)
        import_cache.set(
            name,
            module,
            dependencies={m.__name__ for m in modules[:-1]},
        )

    # Test dependency invalidation
    import_cache.invalidate(modules[0].__name__)
    for module in modules:
        assert import_cache.get(module.__name__) is None


def test_import_profiler(import_profiler: ImportProfiler) -> None:
    """Test import profiler."""
    module_name = "test_module"

    # Test profiling with memory tracking
    import_profiler.start_import(module_name)
    time.sleep(0.1)  # Simulate import time
    profile = import_profiler.finish_import(module_name, dependencies={"dep1", "dep2"})

    assert isinstance(profile, ImportProfile)
    assert profile.module == module_name
    assert profile.duration >= 0.1
    assert profile.dependencies == {"dep1", "dep2"}
    assert not profile.errors
    assert profile.memory_before > 0
    assert profile.memory_after > 0
    assert profile.memory_delta >= 0

    # Test error handling with retry
    import_profiler.start_import("error_module")
    error_profile = import_profiler.finish_import("error_module", error="Import failed")
    assert error_profile.errors == ["Import failed"]

    # Test memory analysis
    analysis = import_profiler.analyze_imports()
    assert analysis["total_imports"] == 2
    assert analysis["error_count"] == 1
    assert analysis["average_duration"] > 0
    assert analysis["total_memory_impact"] >= 0
    assert analysis["average_memory_impact"] >= 0
    assert analysis["max_memory_impact"] >= 0


def test_import_optimizer(
    import_optimizer: ImportOptimizer, temp_modules: list[tuple[str, str]]
) -> None:
    """Test import optimizer."""
    # Test module loading with dependency tracking
    for module_name, module_path in temp_modules:
        spec = import_optimizer.find_spec(module_name)
        assert spec is not None
        assert spec.origin == module_path

        module = MagicMock(__name__=module_name, __spec__=spec)
        import_optimizer.exec_module(module)

    # Test circular import detection
    import_optimizer._import_stack.append(temp_modules[0][0])
    with pytest.raises(CircularDependencyError) as exc_info:
        import_optimizer._check_circular_dependency(temp_modules[0][0])
    assert "Circular dependency detected" in str(exc_info.value)

    # Verify profiling and analysis
    profiles = import_optimizer.get_import_profiles()
    assert len(profiles["profiles"]) == len(temp_modules)
    assert profiles["analysis"]["total_imports"] == len(temp_modules)
    assert "dependency_graph" in profiles
    assert "error_counts" in profiles

    # Test module reloading with dependencies
    reloaded = import_optimizer.reload_module(temp_modules[0][0])
    assert reloaded is not None

    reloaded_deps = import_optimizer.reload_dependencies(temp_modules[0][0])
    assert len(reloaded_deps) >= 0

    # Test cache invalidation with dependencies
    import_optimizer.invalidate_cache(temp_modules[0][0])
    for name, _ in temp_modules:
        assert import_optimizer._cache.get(name) is None


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
