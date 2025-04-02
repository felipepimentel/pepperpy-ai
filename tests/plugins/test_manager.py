"""Tests for the plugin manager module."""

from unittest.mock import AsyncMock, patch

import pytest

from pepperpy.core.errors import ConfigurationError, ValidationError
from pepperpy.plugins.manager import (
    DependencyGraph,
    DependencyType,
    PluginManager,
    get_plugin_manager,
)
from pepperpy.plugins.plugin import PepperpyPlugin


# Mock plugin classes for testing
class MockBasePlugin(PepperpyPlugin):
    """Base mock plugin for testing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_called = False
        self.cleanup_called = False

    async def initialize(self):
        self.init_called = True
        self.initialized = True

    async def cleanup(self):
        self.cleanup_called = True
        self.initialized = False


class MockPluginA(MockBasePlugin):
    """Mock plugin A for testing."""

    pass


class MockPluginB(MockBasePlugin):
    """Mock plugin B for testing."""

    pass


class MockPluginC(MockBasePlugin):
    """Mock plugin C for testing."""

    pass


class TestDependencyGraph:
    """Test cases for the DependencyGraph class."""

    def setup_method(self):
        """Setup before each test."""
        self.graph = DependencyGraph()

    def test_add_dependency(self):
        """Test adding a dependency."""
        # Add dependency
        self.graph.add_dependency("A", "a", "B", "b")

        # Check dependency is added
        deps = self.graph.get_dependencies("A", "a")
        assert len(deps) == 1
        assert deps[0] == ("B", "b")

        # Check reverse dependency is added
        dependents = self.graph.get_dependents("B", "b")
        assert len(dependents) == 1
        assert dependents[0] == ("A", "a")

    def test_get_dependencies_by_type(self):
        """Test getting dependencies by type."""
        # Add dependencies of different types
        self.graph.add_dependency("A", "a", "B", "b", DependencyType.REQUIRED)
        self.graph.add_dependency("A", "a", "C", "c", DependencyType.OPTIONAL)

        # Get all dependencies
        all_deps = self.graph.get_dependencies("A", "a")
        assert len(all_deps) == 2
        assert ("B", "b") in all_deps
        assert ("C", "c") in all_deps

        # Get only required dependencies
        req_deps = self.graph.get_dependencies("A", "a", DependencyType.REQUIRED)
        assert len(req_deps) == 1
        assert req_deps[0] == ("B", "b")

        # Get only optional dependencies
        opt_deps = self.graph.get_dependencies("A", "a", DependencyType.OPTIONAL)
        assert len(opt_deps) == 1
        assert opt_deps[0] == ("C", "c")

    def test_get_dependency_type(self):
        """Test getting dependency type."""
        # Add dependencies of different types
        self.graph.add_dependency("A", "a", "B", "b", DependencyType.REQUIRED)
        self.graph.add_dependency("A", "a", "C", "c", DependencyType.OPTIONAL)

        # Check dependency types
        assert (
            self.graph.get_dependency_type("A", "a", "B", "b")
            == DependencyType.REQUIRED
        )
        assert (
            self.graph.get_dependency_type("A", "a", "C", "c")
            == DependencyType.OPTIONAL
        )
        assert self.graph.get_dependency_type("A", "a", "D", "d") is None

    def test_topological_sort(self):
        """Test topological sorting."""
        # Create a graph with dependencies
        # A depends on B, B depends on C
        self.graph.add_dependency("A", "a", "B", "b")
        self.graph.add_dependency("B", "b", "C", "c")

        # Get topological sort (C, B, A)
        sorted_nodes = self.graph.topological_sort()

        # Check order
        c_index = sorted_nodes.index(("C", "c"))
        b_index = sorted_nodes.index(("B", "b"))
        a_index = sorted_nodes.index(("A", "a"))

        assert c_index < b_index < a_index

    def test_reverse_topological_sort(self):
        """Test reverse topological sorting."""
        # Create a graph with dependencies
        # A depends on B, B depends on C
        self.graph.add_dependency("A", "a", "B", "b")
        self.graph.add_dependency("B", "b", "C", "c")

        # Get reverse topological sort (A, B, C)
        sorted_nodes = self.graph.reverse_topological_sort()

        # Check order
        a_index = sorted_nodes.index(("A", "a"))
        b_index = sorted_nodes.index(("B", "b"))
        c_index = sorted_nodes.index(("C", "c"))

        assert a_index < b_index < c_index

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        # Create a circular dependency
        # A depends on B, B depends on C, C depends on A
        self.graph.add_dependency("A", "a", "B", "b")
        self.graph.add_dependency("B", "b", "C", "c")
        self.graph.add_dependency("C", "c", "A", "a")

        # Topological sort should raise an error
        with pytest.raises(ValueError) as excinfo:
            self.graph.topological_sort()

        assert "Circular dependency detected" in str(excinfo.value)


class TestPluginManager:
    """Test cases for the PluginManager class."""

    def setup_method(self):
        """Setup before each test."""
        self.manager = PluginManager()

        # Mock plugin registry
        patcher = patch("pepperpy.plugins.manager.get_plugin")
        self.mock_get_plugin = patcher.start()
        self.addCleanup(patcher.stop)

        # Setup mock plugins
        self.mock_get_plugin.side_effect = self._mock_get_plugin
        self.plugin_classes = {
            ("A", "a"): MockPluginA,
            ("B", "b"): MockPluginB,
            ("C", "c"): MockPluginC,
        }
        self.plugin_instances = {}

    def addCleanup(self, func):
        """Add cleanup function."""
        # This method is just for compatibility with unittest.TestCase
        # In pytest, we can use the yield fixture, but for simplicity,
        # we'll just call all cleanup functions in teardown_method
        if not hasattr(self, "_cleanup_funcs"):
            self._cleanup_funcs = []
        self._cleanup_funcs.append(func)

    def teardown_method(self):
        """Teardown after each test."""
        if hasattr(self, "_cleanup_funcs"):
            for func in self._cleanup_funcs:
                func()

    def _mock_get_plugin(self, plugin_type, provider_type):
        """Mock implementation of get_plugin."""
        return self.plugin_classes.get((plugin_type, provider_type))

    async def test_create_instance(self):
        """Test creating a plugin instance."""
        # Create an instance
        instance = self.manager.create_instance("A", "a")

        # Check instance is created
        assert isinstance(instance, MockPluginA)
        assert self.manager.get_instance("A", "a") is instance

    async def test_create_instance_with_config(self):
        """Test creating a plugin instance with configuration."""

        # Create a configurable plugin class
        class ConfigurablePlugin(MockBasePlugin):
            param1: str = "default"
            param2: int = 42

        self.plugin_classes[("config", "test")] = ConfigurablePlugin

        # Create an instance with config
        instance = self.manager.create_instance(
            "config", "test", param1="custom", param2=100
        )

        # Check instance is created with correct config
        assert isinstance(instance, ConfigurablePlugin)
        assert instance.param1 == "custom"
        assert instance.param2 == 100

    async def test_create_instance_missing_plugin(self):
        """Test error when creating instance with missing plugin."""
        # Try to create an instance for a non-existent plugin
        with pytest.raises(ValidationError) as excinfo:
            self.manager.create_instance("missing", "plugin")

        assert "Plugin not found" in str(excinfo.value)

    async def test_initialize_plugins(self):
        """Test initializing plugins."""
        # Create instances
        instance_a = self.manager.create_instance("A", "a")
        instance_b = self.manager.create_instance("B", "b")

        # Initialize manager
        await self.manager.initialize()

        # Check instances are initialized
        assert instance_a.init_called
        assert instance_b.init_called

    async def test_cleanup_plugins(self):
        """Test cleaning up plugins."""
        # Create instances
        instance_a = self.manager.create_instance("A", "a")
        instance_b = self.manager.create_instance("B", "b")

        # Initialize and then cleanup
        await self.manager.initialize()
        await self.manager.cleanup()

        # Check instances are cleaned up
        assert instance_a.cleanup_called
        assert instance_b.cleanup_called

        # Check instances are removed
        assert len(self.manager._instances) == 0

    async def test_initialization_order(self):
        """Test initialization order based on dependencies."""
        # Register plugin metadata with dependencies
        self.manager.register_plugin_metadata(
            "A", "a", {"dependencies": [{"type": "B", "provider": "b"}]}
        )
        self.manager.register_plugin_metadata(
            "B", "b", {"dependencies": [{"type": "C", "provider": "c"}]}
        )

        # Create instances
        instance_a = self.manager.create_instance("A", "a")
        instance_b = self.manager.create_instance("B", "b")
        instance_c = self.manager.create_instance("C", "c")

        # Track initialization order
        init_order = []

        # Mock initialize methods to track order
        async def mock_initialize(instance):
            init_order.append(instance)
            instance.initialized = True

        with patch.object(
            MockPluginA, "initialize", new_callable=AsyncMock
        ) as mock_a_init, patch.object(
            MockPluginB, "initialize", new_callable=AsyncMock
        ) as mock_b_init, patch.object(
            MockPluginC, "initialize", new_callable=AsyncMock
        ) as mock_c_init:
            mock_a_init.side_effect = lambda: mock_initialize(instance_a)
            mock_b_init.side_effect = lambda: mock_initialize(instance_b)
            mock_c_init.side_effect = lambda: mock_initialize(instance_c)

            # Initialize manager
            await self.manager.initialize()

            # Check initialization order
            assert init_order == [instance_c, instance_b, instance_a]

    async def test_shutdown_order(self):
        """Test shutdown order based on dependencies."""
        # Register plugin metadata with dependencies
        self.manager.register_plugin_metadata(
            "A", "a", {"dependencies": [{"type": "B", "provider": "b"}]}
        )
        self.manager.register_plugin_metadata(
            "B", "b", {"dependencies": [{"type": "C", "provider": "c"}]}
        )

        # Create instances
        instance_a = self.manager.create_instance("A", "a")
        instance_b = self.manager.create_instance("B", "b")
        instance_c = self.manager.create_instance("C", "c")

        # Track cleanup order
        cleanup_order = []

        # Mock cleanup methods to track order
        async def mock_cleanup(instance):
            cleanup_order.append(instance)
            instance.initialized = False

        with patch.object(
            MockPluginA, "cleanup", new_callable=AsyncMock
        ) as mock_a_cleanup, patch.object(
            MockPluginB, "cleanup", new_callable=AsyncMock
        ) as mock_b_cleanup, patch.object(
            MockPluginC, "cleanup", new_callable=AsyncMock
        ) as mock_c_cleanup:
            mock_a_cleanup.side_effect = lambda: mock_cleanup(instance_a)
            mock_b_cleanup.side_effect = lambda: mock_cleanup(instance_b)
            mock_c_cleanup.side_effect = lambda: mock_cleanup(instance_c)

            # Initialize and cleanup manager
            await self.manager.initialize()
            await self.manager.cleanup()

            # Check cleanup order (reverse of initialization)
            assert cleanup_order == [instance_a, instance_b, instance_c]

    async def test_load_dependencies(self):
        """Test loading dependencies."""
        # Register plugin metadata with dependencies
        self.manager.register_plugin_metadata(
            "A",
            "a",
            {
                "dependencies": [
                    {"type": "B", "provider": "b"},
                    {"type": "C", "provider": "c", "dependency_type": "optional"},
                ]
            },
        )

        # Load dependencies
        dependencies = await self.manager.load_dependencies("A", "a")

        # Check dependencies are loaded
        assert ("B", "b") in dependencies
        assert ("C", "c") in dependencies

        # Check instances are created and initialized
        instance_b = self.manager.get_instance("B", "b")
        instance_c = self.manager.get_instance("C", "c")

        assert isinstance(instance_b, MockPluginB)
        assert isinstance(instance_c, MockPluginC)
        assert instance_b.init_called
        assert instance_c.init_called

    async def test_load_dependencies_with_missing_required(self):
        """Test error when loading missing required dependency."""
        # Register plugin metadata with dependencies
        self.manager.register_plugin_metadata(
            "A", "a", {"dependencies": [{"type": "missing", "provider": "required"}]}
        )

        # Try to load dependencies
        with pytest.raises(ConfigurationError) as excinfo:
            await self.manager.load_dependencies("A", "a")

        assert "Failed to load required dependency" in str(excinfo.value)

    async def test_load_dependencies_with_missing_optional(self):
        """Test handling missing optional dependency."""
        # Register plugin metadata with dependencies
        self.manager.register_plugin_metadata(
            "A",
            "a",
            {
                "dependencies": [
                    {
                        "type": "missing",
                        "provider": "optional",
                        "dependency_type": "optional",
                    }
                ]
            },
        )

        # Load dependencies
        dependencies = await self.manager.load_dependencies("A", "a")

        # Check no dependencies are loaded
        assert len(dependencies) == 0

    def test_get_plugin_manager(self):
        """Test getting global plugin manager."""
        # Reset the global plugin manager
        import pepperpy.plugins.manager

        pepperpy.plugins.manager._plugin_manager = None

        # Get plugin manager
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        # Check both are the same instance
        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)
