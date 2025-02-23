"""Tests for import hook utilities."""

import importlib.abc
import importlib.machinery
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.utils.imports_hook import ImportCache, ImportHookError, ImportOptimizer
from pepperpy.utils.modules import ModuleManager


@pytest.fixture
def module_manager() -> ModuleManager:
    """Create module manager fixture.

    Returns:
        Module manager instance
    """
    return ModuleManager()


@pytest.fixture
def import_cache() -> ImportCache:
    """Create import cache fixture.

    Returns:
        Import cache instance
    """
    return ImportCache()


@pytest.fixture
def import_optimizer(module_manager: ModuleManager) -> ImportOptimizer:
    """Create import optimizer fixture.

    Args:
        module_manager: Module manager fixture

    Returns:
        Import optimizer instance
    """
    return ImportOptimizer(module_manager)


def test_import_hook_error():
    """Test import hook error."""
    error = ImportHookError("test error", "test_module")
    assert str(error) == "test error"
    assert error.module == "test_module"
    assert error.details == {}

    error = ImportHookError("test error", "test_module", {"key": "value"})
    assert error.details == {"key": "value"}


def test_import_cache_initialization(import_cache: ImportCache):
    """Test import cache initialization.

    Args:
        import_cache: Import cache fixture
    """
    assert isinstance(import_cache._cache, dict)
    assert isinstance(import_cache._dependencies, dict)
    assert isinstance(import_cache._loading, set)


def test_import_cache_get_set(import_cache: ImportCache):
    """Test import cache get and set operations.

    Args:
        import_cache: Import cache fixture
    """
    # Create mock module
    module = MagicMock(spec=ModuleType)
    module.__name__ = "test_module"

    # Test get nonexistent module
    assert import_cache.get("test_module") is None

    # Test set module without dependencies
    import_cache.set("test_module", module)
    assert import_cache.get("test_module") == module
    assert "test_module" not in import_cache._dependencies

    # Test set module with dependencies
    import_cache.set("test_module", module, {"dep1", "dep2"})
    assert import_cache.get("test_module") == module
    assert import_cache._dependencies["test_module"] == {"dep1", "dep2"}


def test_import_cache_loading(import_cache: ImportCache):
    """Test import cache loading operations.

    Args:
        import_cache: Import cache fixture
    """
    # Test loading state
    assert not import_cache.is_loading("test_module")

    # Test start loading
    import_cache.start_loading("test_module")
    assert import_cache.is_loading("test_module")

    # Test finish loading
    import_cache.finish_loading("test_module")
    assert not import_cache.is_loading("test_module")


def test_import_cache_clear(import_cache: ImportCache):
    """Test import cache clear operation.

    Args:
        import_cache: Import cache fixture
    """
    # Add module to cache
    module = MagicMock(spec=ModuleType)
    module.__name__ = "test_module"
    import_cache.set("test_module", module, {"dep1", "dep2"})
    import_cache.start_loading("test_module")

    # Clear cache
    import_cache.clear()
    assert len(import_cache._cache) == 0
    assert len(import_cache._dependencies) == 0
    assert len(import_cache._loading) == 0


def test_import_optimizer_initialization(import_optimizer: ImportOptimizer):
    """Test import optimizer initialization.

    Args:
        import_optimizer: Import optimizer fixture
    """
    assert isinstance(import_optimizer._manager, ModuleManager)
    assert isinstance(import_optimizer._cache, ImportCache)
    assert isinstance(import_optimizer._hooks, list)


def test_import_optimizer_hooks(import_optimizer: ImportOptimizer):
    """Test import optimizer hook operations.

    Args:
        import_optimizer: Import optimizer fixture
    """
    # Create mock hook
    hook = MagicMock(spec=importlib.abc.MetaPathFinder)

    # Test register hook
    import_optimizer.register_hook(hook)
    assert hook in import_optimizer._hooks
    assert hook in sys.meta_path

    # Test register duplicate hook
    import_optimizer.register_hook(hook)
    assert len([h for h in import_optimizer._hooks if h == hook]) == 1

    # Test unregister hook
    import_optimizer.unregister_hook(hook)
    assert hook not in import_optimizer._hooks
    assert hook not in sys.meta_path

    # Test unregister nonexistent hook
    import_optimizer.unregister_hook(hook)  # Should not raise


@patch("pathlib.Path.is_file")
def test_import_optimizer_find_spec(
    mock_is_file: MagicMock,
    import_optimizer: ImportOptimizer,
):
    """Test import optimizer find_spec operation.

    Args:
        mock_is_file: Mock is_file
        import_optimizer: Import optimizer fixture
    """
    # Test cached module
    module = MagicMock(spec=ModuleType)
    module.__name__ = "test_module"
    import_optimizer._cache.set("test_module", module)
    assert import_optimizer.find_spec("test_module") is None

    # Test circular import
    import_optimizer._cache.start_loading("test_module")
    with pytest.raises(ImportHookError) as exc_info:
        import_optimizer.find_spec("test_module")
    assert "Circular import detected" in str(exc_info.value)
    import_optimizer._cache.finish_loading("test_module")

    # Test source file
    mock_is_file.side_effect = [True, False]
    spec = import_optimizer.find_spec("test_module")
    assert spec is not None
    assert spec.name == "test_module"
    assert spec.loader == import_optimizer
    assert spec.origin is not None
    assert spec.origin.endswith("test_module.py")

    # Test package directory
    mock_is_file.side_effect = [False, True]
    spec = import_optimizer.find_spec("test_package")
    assert spec is not None
    assert spec.name == "test_package"
    assert spec.loader == import_optimizer
    assert spec.origin is not None
    assert spec.origin.endswith("__init__.py")
    assert spec.submodule_search_locations is not None

    # Test module not found
    mock_is_file.side_effect = [False, False]
    assert import_optimizer.find_spec("nonexistent") is None


def test_import_optimizer_create_module(import_optimizer: ImportOptimizer):
    """Test import optimizer create_module operation.

    Args:
        import_optimizer: Import optimizer fixture
    """
    # Create mock spec
    spec = MagicMock(spec=importlib.machinery.ModuleSpec)
    spec.name = "test_module"

    # Test create module
    assert import_optimizer.create_module(spec) is None


@patch("pathlib.Path.read_text")
def test_import_optimizer_exec_module(
    mock_read_text: MagicMock,
    import_optimizer: ImportOptimizer,
):
    """Test import optimizer exec_module operation.

    Args:
        mock_read_text: Mock read_text
        import_optimizer: Import optimizer fixture
    """
    # Create mock module
    module = MagicMock(spec=ModuleType)
    module.__name__ = "test_module"
    module.__dict__ = {}
    module.__spec__ = MagicMock(spec=importlib.machinery.ModuleSpec)
    module.__spec__.origin = "/test/path/test_module.py"

    # Test successful execution
    mock_read_text.return_value = "x = 1"
    import_optimizer.exec_module(module)
    assert module.__dict__["x"] == 1
    assert not import_optimizer._cache.is_loading("test_module")
    assert import_optimizer._cache.get("test_module") == module

    # Test invalid spec
    module.__spec__ = None
    with pytest.raises(ImportHookError) as exc_info:
        import_optimizer.exec_module(module)
    assert "Invalid module specification" in str(exc_info.value)

    # Test execution error
    module.__spec__ = MagicMock(spec=importlib.machinery.ModuleSpec)
    module.__spec__.origin = "/test/path/test_module.py"
    mock_read_text.side_effect = Exception("test error")
    with pytest.raises(ImportHookError) as exc_info:
        import_optimizer.exec_module(module)
    assert "Failed to execute module" in str(exc_info.value)


def test_import_optimizer_invalidate_caches(import_optimizer: ImportOptimizer):
    """Test import optimizer invalidate_caches operation.

    Args:
        import_optimizer: Import optimizer fixture
    """
    # Create mock hook
    hook = MagicMock(spec=importlib.abc.MetaPathFinder)
    import_optimizer.register_hook(hook)

    # Add module to cache
    module = MagicMock(spec=ModuleType)
    module.__name__ = "test_module"
    import_optimizer._cache.set("test_module", module)

    # Invalidate caches
    import_optimizer.invalidate_caches()
    assert len(import_optimizer._cache._cache) == 0
    hook.invalidate_caches.assert_called_once()


def test_import_optimizer_get_code(import_optimizer: ImportOptimizer):
    """Test import optimizer get_code operation.

    Args:
        import_optimizer: Import optimizer fixture
    """
    assert import_optimizer.get_code("test_module") is None
