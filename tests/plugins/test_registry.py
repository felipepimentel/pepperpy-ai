"""Tests for the plugin registry module."""

import os
import tempfile
from pathlib import Path

import pytest

from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.registry import (
    PluginError,
    _resolve_alias,
    clear_path_cache,
    create_provider_instance,
    discover_plugins,
    find_fallback,
    get_plugin,
    load_plugin,
    register_plugin,
    register_plugin_alias,
    register_plugin_fallbacks,
    register_plugin_path,
)


# Mock plugin classes for testing
class MockPlugin(PepperpyPlugin):
    """Mock plugin for testing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def initialize(self):
        self.initialized = True

    async def cleanup(self):
        self.initialized = False


class MockLLMPlugin(PepperpyPlugin):
    """Mock LLM plugin for testing."""

    model: str = "default-model"
    temperature: float = 0.7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def initialize(self):
        self.initialized = True

    async def cleanup(self):
        self.initialized = False


class TestPluginRegistry:
    """Test cases for the plugin registry module."""

    def setup_method(self):
        """Setup before each test."""
        # Create a temp directory for test plugins
        self.temp_dir = tempfile.TemporaryDirectory()
        self.plugin_dir = Path(self.temp_dir.name) / "plugins"
        os.makedirs(self.plugin_dir, exist_ok=True)

        # Clear plugin registry before each test
        from pepperpy.plugins.registry import (
            _plugin_metadata,
            _plugin_paths,
            _plugin_registry,
        )

        _plugin_registry.clear()
        _plugin_metadata.clear()
        _plugin_paths.clear()
        clear_path_cache()

    def teardown_method(self):
        """Teardown after each test."""
        # Remove the temp directory
        self.temp_dir.cleanup()

    def test_register_plugin(self):
        """Test registering a plugin."""
        # Register a plugin
        register_plugin("test", "mock", MockPlugin)

        # Check if plugin is registered
        plugin_class = get_plugin("test", "mock")
        assert plugin_class is MockPlugin

    def test_register_plugin_with_metadata(self):
        """Test registering a plugin with metadata."""
        # Register a plugin with metadata
        metadata = {
            "name": "Mock Plugin",
            "version": "1.0.0",
            "description": "A mock plugin for testing",
            "author": "Test Author",
        }
        register_plugin("test", "mock", MockPlugin, metadata)

        # Check if plugin is registered with metadata
        plugin_class = get_plugin("test", "mock")
        assert plugin_class is MockPlugin

        # Check if metadata is registered
        from pepperpy.plugins.registry import get_plugin_metadata

        plugin_metadata = get_plugin_metadata("test", "mock")
        assert plugin_metadata == metadata

    def test_register_plugin_alias(self):
        """Test registering a plugin alias."""
        # Register a plugin
        register_plugin("llm", "openai", MockLLMPlugin)

        # Register an alias
        register_plugin_alias("llm", "gpt4", "openai", {"model": "gpt-4"})

        # Check if alias resolves to the right plugin
        plugin_class = get_plugin("llm", "gpt4")
        assert plugin_class is MockLLMPlugin

        # Test alias resolution
        provider, config = _resolve_alias("llm", "gpt4")
        assert provider == "openai"
        assert config == {"model": "gpt-4"}

    def test_register_fallbacks(self):
        """Test registering fallbacks."""
        # Register plugins
        register_plugin("llm", "openai", MockLLMPlugin)
        register_plugin("llm", "anthropic", MockLLMPlugin)

        # Register fallbacks
        register_plugin_fallbacks("llm", ["anthropic", "openai"])

        # Check fallbacks work when primary is missing
        fallback = find_fallback("llm", "missing")
        assert fallback == "anthropic"

        # Remove first fallback and check next one is used
        from pepperpy.plugins.registry import _plugin_registry

        del _plugin_registry["llm"]["anthropic"]

        fallback = find_fallback("llm", "missing")
        assert fallback == "openai"

    def test_create_provider_instance(self):
        """Test creating a provider instance."""
        # Register a plugin
        register_plugin("llm", "test", MockLLMPlugin)

        # Create an instance
        instance = create_provider_instance("llm", "test", temperature=0.5)

        # Check instance is created with correct config
        assert isinstance(instance, MockLLMPlugin)
        assert instance.temperature == 0.5
        assert instance.model == "default-model"  # Default value

    def test_provider_instance_with_alias(self):
        """Test creating a provider instance with an alias."""
        # Register a plugin
        register_plugin("llm", "openai", MockLLMPlugin)

        # Register an alias
        register_plugin_alias("llm", "gpt4", "openai", {"model": "gpt-4"})

        # Create an instance using the alias
        instance = create_provider_instance("llm", "gpt4", temperature=0.5)

        # Check instance is created with correct config including alias override
        assert isinstance(instance, MockLLMPlugin)
        assert instance.temperature == 0.5
        assert instance.model == "gpt-4"  # From alias

    def test_provider_instance_with_missing_plugin(self):
        """Test error when creating instance with missing plugin."""
        # Try to create an instance for a non-existent plugin
        with pytest.raises(PluginError) as excinfo:
            create_provider_instance("missing", "provider")

        assert "Provider not found" in str(excinfo.value)

    def test_load_plugin(self):
        """Test loading a plugin."""
        # Create plugin directory structure
        plugin_type = "test"
        provider_type = "yaml"
        plugin_path = self.plugin_dir / plugin_type / provider_type
        os.makedirs(plugin_path, exist_ok=True)

        # Create a mock plugin.yaml file
        with open(plugin_path / "plugin.yaml", "w") as f:
            f.write(
                """
name: Test Plugin
version: 1.0.0
description: A test plugin
entry_point: plugin_module:TestPlugin
            """
            )

        # Create a mock plugin module
        module_dir = self.plugin_dir / "plugin_module"
        os.makedirs(module_dir, exist_ok=True)

        with open(module_dir / "__init__.py", "w") as f:
            f.write("")

        with open(module_dir / "__init__.py", "w") as f:
            f.write(
                """
from pepperpy.plugins.plugin import PepperpyPlugin

class TestPlugin(PepperpyPlugin):
    async def initialize(self):
        self.initialized = True
        
    async def cleanup(self):
        self.initialized = False
            """
            )

        # Register plugin path and try to load
        register_plugin_path(str(self.plugin_dir))

        # This will fail since the module can't be imported in the test environment,
        # but we can test the error handling
        result = load_plugin(plugin_type, provider_type)
        assert result is None

    def test_discovery(self):
        """Test plugin discovery."""
        # Create plugin directory structure
        for plugin_type in ["llm", "embeddings"]:
            for provider_type in ["test1", "test2"]:
                plugin_path = self.plugin_dir / plugin_type / provider_type
                os.makedirs(plugin_path, exist_ok=True)

                # Create a mock plugin.yaml file
                with open(plugin_path / "plugin.yaml", "w") as f:
                    f.write(
                        f"""
name: {plugin_type.capitalize()} {provider_type.capitalize()} Plugin
version: 1.0.0
description: A test {plugin_type} plugin
entry_point: provider:Plugin
                    """
                    )

        # Register plugin path
        register_plugin_path(str(self.plugin_dir))

        # Discover plugins
        plugins = discover_plugins()

        # Check if plugins were discovered
        assert "llm" in plugins
        assert "embeddings" in plugins
        assert "test1" in plugins["llm"]
        assert "test2" in plugins["llm"]
        assert "test1" in plugins["embeddings"]
        assert "test2" in plugins["embeddings"]

        # Check metadata
        assert plugins["llm"]["test1"]["name"] == "Llm Test1 Plugin"
        assert plugins["embeddings"]["test2"]["name"] == "Embeddings Test2 Plugin"
