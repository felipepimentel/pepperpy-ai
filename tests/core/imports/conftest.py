"""Test fixtures for the imports module."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Generator, List, Set
from unittest.mock import AsyncMock, Mock

import pytest

from pepperpy.core.imports import ImportManager, ImportOptimizer


@pytest.fixture
def test_module_path(tmp_path: Path) -> Path:
    """Create a test module for importing."""
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        """
def test_function():
    return "test"

class TestClass:
    def method(self):
        return "test"

TEST_CONSTANT = "test"
"""
    )
    return module_path


@pytest.fixture
def test_package_path(tmp_path: Path) -> Path:
    """Create a test package for importing."""
    package_path = tmp_path / "test_package"
    package_path.mkdir()
    init_path = package_path / "__init__.py"
    init_path.write_text(
        """
from .module import test_function, TestClass, TEST_CONSTANT

__all__ = ["test_function", "TestClass", "TEST_CONSTANT"]
"""
    )
    module_path = package_path / "module.py"
    module_path.write_text(
        """
def test_function():
    return "test"

class TestClass:
    def method(self):
        return "test"

TEST_CONSTANT = "test"
"""
    )
    return package_path


@pytest.fixture
def mock_module_manager() -> Mock:
    """Create a mock module manager."""
    manager = Mock()
    manager.get_module.return_value = None
    manager.get_dependencies.return_value = set()
    return manager


@pytest.fixture
def mock_profiler() -> Mock:
    """Create a mock import profiler."""
    profiler = Mock()
    profiler.start_import.return_value = None
    profiler.finish_import.return_value = {"duration": 0.1, "size": 1024}
    return profiler


@pytest.fixture
def mock_monitoring() -> Mock:
    """Create a mock monitoring manager."""
    monitoring = Mock()
    monitoring.record_import = AsyncMock()
    monitoring.record_error = AsyncMock()
    return monitoring


@pytest.fixture
def import_manager(
    mock_module_manager: Mock,
    mock_profiler: Mock,
    mock_monitoring: Mock,
) -> ImportManager:
    """Create an import manager with mocked dependencies."""
    manager = ImportManager()
    manager._module_manager = mock_module_manager
    manager._profiler = mock_profiler
    manager._monitoring = mock_monitoring
    return manager


@pytest.fixture
def import_optimizer(
    mock_module_manager: Mock,
) -> ImportOptimizer:
    """Create an import optimizer with mocked dependencies."""
    optimizer = ImportOptimizer()
    optimizer._module_manager = mock_module_manager
    return optimizer


@pytest.fixture(autouse=True)
def cleanup_sys_modules() -> Generator[None, None, None]:
    """Clean up test modules from sys.modules after each test."""
    original_modules = set(sys.modules.keys())
    yield
    current_modules = set(sys.modules.keys())
    test_modules = current_modules - original_modules
    for module_name in test_modules:
        sys.modules.pop(module_name, None)


@pytest.fixture(autouse=True)
def cleanup_sys_path() -> Generator[None, None, None]:
    """Clean up test paths from sys.path after each test."""
    original_path = list(sys.path)
    yield
    sys.path[:] = original_path 