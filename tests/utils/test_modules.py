"""Tests for module management utilities."""

from types import ModuleType
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest

from pepperpy.utils.modules import ModuleError, ModuleInfo, ModuleManager


@pytest.fixture
def module_manager() -> ModuleManager:
    """Create module manager fixture.

    Returns:
        Module manager instance
    """
    return ModuleManager()


@pytest.fixture
def mock_module() -> ModuleType:
    """Create mock module fixture.

    Returns:
        Mock module instance
    """
    module = MagicMock(spec=ModuleType)
    module.__name__ = "test_module"
    return module


def test_module_info_creation():
    """Test module info creation."""
    info = ModuleInfo(name="test")
    assert info.name == "test"
    assert info.path is None
    assert info.version is None
    assert info.doc is None
    assert info.dependencies == set()
    assert info.attributes == {}
    assert info.metadata == {}


def test_module_error_creation():
    """Test module error creation."""
    error = ModuleError("test error", "test_module")
    assert str(error) == "test error"
    assert error.module == "test_module"
    assert error.details == {}

    error = ModuleError("test error", "test_module", {"key": "value"})
    assert error.details == {"key": "value"}


def test_module_manager_initialization(module_manager: ModuleManager):
    """Test module manager initialization.

    Args:
        module_manager: Module manager fixture
    """
    assert isinstance(module_manager._modules, dict)
    assert isinstance(module_manager._dependencies, dict)
    assert isinstance(module_manager._reverse_dependencies, dict)


@patch("pepperpy.utils.modules.get_module_path")
@patch("pepperpy.utils.modules.get_module_version")
@patch("pepperpy.utils.modules.get_module_doc")
@patch("pepperpy.utils.modules.get_module_dependencies")
@patch("pepperpy.utils.modules.get_module_attributes")
def test_register_module(
    mock_get_attributes: MagicMock,
    mock_get_dependencies: MagicMock,
    mock_get_doc: MagicMock,
    mock_get_version: MagicMock,
    mock_get_path: MagicMock,
    module_manager: ModuleManager,
    mock_module: ModuleType,
):
    """Test module registration.

    Args:
        mock_get_attributes: Mock get_module_attributes
        mock_get_dependencies: Mock get_module_dependencies
        mock_get_doc: Mock get_module_doc
        mock_get_version: Mock get_module_version
        mock_get_path: Mock get_module_path
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Setup mocks
    mock_get_path.return_value = "/test/path"
    mock_get_version.return_value = "1.0.0"
    mock_get_doc.return_value = "Test module"
    mock_get_dependencies.return_value = {"dep1", "dep2"}
    mock_get_attributes.return_value = {"attr1": "value1"}

    # Register module
    info = module_manager.register_module(mock_module, {"meta": "data"})

    # Verify module info
    assert info.name == "test_module"
    assert info.path == "/test/path"
    assert info.version == "1.0.0"
    assert info.doc == "Test module"
    assert info.dependencies == {"dep1", "dep2"}
    assert info.attributes == {"attr1": "value1"}
    assert info.metadata == {"meta": "data"}

    # Verify manager state
    assert module_manager._modules["test_module"] == info
    assert module_manager._dependencies["test_module"] == {"dep1", "dep2"}
    assert module_manager._reverse_dependencies["dep1"] == {"test_module"}
    assert module_manager._reverse_dependencies["dep2"] == {"test_module"}


def test_register_module_error(module_manager: ModuleManager):
    """Test module registration error.

    Args:
        module_manager: Module manager fixture
    """
    # Create an invalid module without __name__ attribute
    invalid_module = MagicMock(spec=ModuleType)
    delattr(invalid_module, "__name__")  # Remove __name__ attribute

    with pytest.raises(ModuleError) as exc_info:
        module_manager.register_module(invalid_module)

    assert "Failed to register module" in str(exc_info.value)


def test_unregister_module(module_manager: ModuleManager, mock_module: ModuleType):
    """Test module unregistration.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module first
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        mock_get_deps.return_value = {"dep1", "dep2"}
        module_manager.register_module(mock_module)

    # Unregister module
    module_manager.unregister_module("test_module")

    # Verify manager state
    assert "test_module" not in module_manager._modules
    assert "test_module" not in module_manager._dependencies
    assert "test_module" not in module_manager._reverse_dependencies["dep1"]
    assert "test_module" not in module_manager._reverse_dependencies["dep2"]


def test_unregister_nonexistent_module(module_manager: ModuleManager):
    """Test unregistering nonexistent module.

    Args:
        module_manager: Module manager fixture
    """
    with pytest.raises(ModuleError) as exc_info:
        module_manager.unregister_module("nonexistent")

    assert "Module not found" in str(exc_info.value)


def test_get_module_info(module_manager: ModuleManager, mock_module: ModuleType):
    """Test getting module information.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    info = module_manager.register_module(mock_module)

    # Get module info
    retrieved_info = module_manager.get_module_info("test_module")
    assert retrieved_info == info

    # Get nonexistent module info
    assert module_manager.get_module_info("nonexistent") is None


def test_get_dependencies(module_manager: ModuleManager, mock_module: ModuleType):
    """Test getting module dependencies.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        mock_get_deps.return_value = {"dep1", "dep2"}
        module_manager.register_module(mock_module)

    # Get dependencies
    deps = module_manager.get_dependencies("test_module")
    assert deps == {"dep1", "dep2"}

    # Get nonexistent module dependencies
    with pytest.raises(ModuleError) as exc_info:
        module_manager.get_dependencies("nonexistent")

    assert "Module not found" in str(exc_info.value)


def test_get_reverse_dependencies(
    module_manager: ModuleManager, mock_module: ModuleType
):
    """Test getting reverse dependencies.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register modules
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        mock_get_deps.return_value = {"dep1"}
        module_manager.register_module(mock_module)

        mock_module2 = MagicMock(spec=ModuleType)
        mock_module2.__name__ = "test_module2"
        mock_get_deps.return_value = {"dep1"}
        module_manager.register_module(mock_module2)

    # Get reverse dependencies
    rev_deps = module_manager.get_reverse_dependencies("dep1")
    assert rev_deps == {"test_module", "test_module2"}

    # Get nonexistent module reverse dependencies
    with pytest.raises(ModuleError) as exc_info:
        module_manager.get_reverse_dependencies("nonexistent")

    assert "Module not found" in str(exc_info.value)


def test_get_all_dependencies(module_manager: ModuleManager):
    """Test getting all dependencies recursively.

    Args:
        module_manager: Module manager fixture
    """
    # Register modules with dependencies
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        # Module A depends on B and C
        mock_module_a = MagicMock(spec=ModuleType)
        mock_module_a.__name__ = "module_a"
        mock_get_deps.return_value = {"module_b", "module_c"}
        module_manager.register_module(mock_module_a)

        # Module B depends on D
        mock_module_b = MagicMock(spec=ModuleType)
        mock_module_b.__name__ = "module_b"
        mock_get_deps.return_value = {"module_d"}
        module_manager.register_module(mock_module_b)

        # Module C depends on D and E
        mock_module_c = MagicMock(spec=ModuleType)
        mock_module_c.__name__ = "module_c"
        mock_get_deps.return_value = {"module_d", "module_e"}
        module_manager.register_module(mock_module_c)

    # Get all dependencies
    all_deps = module_manager.get_all_dependencies("module_a")
    assert all_deps == {"module_b", "module_c", "module_d", "module_e"}


def test_get_dependency_order(module_manager: ModuleManager):
    """Test getting modules in dependency order.

    Args:
        module_manager: Module manager fixture
    """
    # Register modules with dependencies
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        # Module A depends on B and C
        mock_module_a = MagicMock(spec=ModuleType)
        mock_module_a.__name__ = "module_a"
        mock_get_deps.return_value = {"module_b", "module_c"}
        module_manager.register_module(mock_module_a)

        # Module B depends on D
        mock_module_b = MagicMock(spec=ModuleType)
        mock_module_b.__name__ = "module_b"
        mock_get_deps.return_value = {"module_d"}
        module_manager.register_module(mock_module_b)

        # Module C depends on D
        mock_module_c = MagicMock(spec=ModuleType)
        mock_module_c.__name__ = "module_c"
        mock_get_deps.return_value = {"module_d"}
        module_manager.register_module(mock_module_c)

        # Module D has no dependencies
        mock_module_d = MagicMock(spec=ModuleType)
        mock_module_d.__name__ = "module_d"
        mock_get_deps.return_value = set()
        module_manager.register_module(mock_module_d)

    # Get dependency order
    order = module_manager.get_dependency_order()

    # Verify order (D should be first, A should be last)
    assert order.index("module_d") < order.index("module_b")
    assert order.index("module_d") < order.index("module_c")
    assert order.index("module_b") < order.index("module_a")
    assert order.index("module_c") < order.index("module_a")


def test_get_dependency_order_circular(module_manager: ModuleManager):
    """Test getting modules with circular dependencies.

    Args:
        module_manager: Module manager fixture
    """
    # Register modules with circular dependencies
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        # Module A depends on B
        mock_module_a = MagicMock(spec=ModuleType)
        mock_module_a.__name__ = "module_a"
        mock_get_deps.return_value = {"module_b"}
        module_manager.register_module(mock_module_a)

        # Module B depends on A
        mock_module_b = MagicMock(spec=ModuleType)
        mock_module_b.__name__ = "module_b"
        mock_get_deps.return_value = {"module_a"}
        module_manager.register_module(mock_module_b)

    # Get dependency order should raise error
    with pytest.raises(ModuleError) as exc_info:
        module_manager.get_dependency_order()

    assert "Circular dependency detected" in str(exc_info.value)


@patch("pepperpy.utils.modules.safe_import")
def test_check_dependencies(
    mock_safe_import: MagicMock,
    module_manager: ModuleManager,
    mock_module: ModuleType,
):
    """Test checking module dependencies.

    Args:
        mock_safe_import: Mock safe_import
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        mock_get_deps.return_value = {"dep1", "dep2"}
        module_manager.register_module(mock_module)

    # Test all dependencies available
    mock_safe_import.return_value = True
    assert module_manager.check_dependencies("test_module") is True

    # Test missing dependency
    mock_safe_import.side_effect = [True, False]
    assert module_manager.check_dependencies("test_module") is False

    # Test nonexistent module
    with pytest.raises(ModuleError) as exc_info:
        module_manager.check_dependencies("nonexistent")

    assert "Module not found" in str(exc_info.value)


@patch("pepperpy.utils.modules.safe_import")
@patch("pepperpy.utils.modules.validate_imports")
def test_validate_module(
    mock_validate_imports: MagicMock,
    mock_safe_import: MagicMock,
    module_manager: ModuleManager,
    mock_module: ModuleType,
):
    """Test validating module.

    Args:
        mock_validate_imports: Mock validate_imports
        mock_safe_import: Mock safe_import
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    module_manager.register_module(mock_module)

    # Test valid module
    mock_safe_import.return_value = mock_module
    mock_validate_imports.return_value = True
    assert module_manager.validate_module("test_module") is True

    # Test invalid module
    mock_validate_imports.return_value = False
    assert module_manager.validate_module("test_module") is False

    # Test import failure
    mock_safe_import.return_value = None
    assert module_manager.validate_module("test_module") is False

    # Test nonexistent module
    with pytest.raises(ModuleError) as exc_info:
        module_manager.validate_module("nonexistent")

    assert "Module not found" in str(exc_info.value)


@patch("pepperpy.utils.modules.safe_import")
@patch("pepperpy.utils.modules.check_circular_imports")
def test_check_circular_imports(
    mock_check_circular: MagicMock,
    mock_safe_import: MagicMock,
    module_manager: ModuleManager,
    mock_module: ModuleType,
):
    """Test checking circular imports.

    Args:
        mock_check_circular: Mock check_circular_imports
        mock_safe_import: Mock safe_import
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    module_manager.register_module(mock_module)

    # Test no circular imports
    mock_safe_import.return_value = mock_module
    mock_check_circular.return_value = []
    assert module_manager.check_circular_imports("test_module") == []

    # Test circular imports found
    circular_imports = [("module1", "module2"), ("module2", "module3")]
    mock_check_circular.return_value = circular_imports
    assert module_manager.check_circular_imports("test_module") == circular_imports

    # Test import failure
    mock_safe_import.return_value = None
    assert module_manager.check_circular_imports("test_module") == []

    # Test nonexistent module
    with pytest.raises(ModuleError) as exc_info:
        module_manager.check_circular_imports("nonexistent")

    assert "Module not found" in str(exc_info.value)


def test_list_modules(module_manager: ModuleManager, mock_module: ModuleType):
    """Test listing registered modules.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register modules
    module_manager.register_module(mock_module)

    mock_module2 = MagicMock(spec=ModuleType)
    mock_module2.__name__ = "test_module2"
    module_manager.register_module(mock_module2)

    # List modules
    modules = module_manager.list_modules()
    assert set(modules) == {"test_module", "test_module2"}


def test_get_module_graph(module_manager: ModuleManager, mock_module: ModuleType):
    """Test getting module dependency graph.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        mock_get_deps.return_value = {"dep1", "dep2"}
        module_manager.register_module(mock_module)

    # Get module graph
    graph = module_manager.get_module_graph()
    assert isinstance(graph, Dict)
    assert graph["test_module"] == {"dep1", "dep2"}


def test_get_reverse_graph(module_manager: ModuleManager, mock_module: ModuleType):
    """Test getting reverse dependency graph.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    with patch("pepperpy.utils.modules.get_module_dependencies") as mock_get_deps:
        mock_get_deps.return_value = {"dep1", "dep2"}
        module_manager.register_module(mock_module)

    # Get reverse graph
    graph = module_manager.get_reverse_graph()
    assert isinstance(graph, Dict)
    assert graph["dep1"] == {"test_module"}
    assert graph["dep2"] == {"test_module"}


def test_clear(module_manager: ModuleManager, mock_module: ModuleType):
    """Test clearing all registered modules.

    Args:
        module_manager: Module manager fixture
        mock_module: Mock module fixture
    """
    # Register module
    module_manager.register_module(mock_module)

    # Clear modules
    module_manager.clear()

    # Verify state
    assert len(module_manager._modules) == 0
    assert len(module_manager._dependencies) == 0
    assert len(module_manager._reverse_dependencies) == 0
