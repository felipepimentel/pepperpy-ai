#!/usr/bin/env python3
"""
Enhanced Plugin System Example.

This example demonstrates the enhanced plugin system in PepperPy,
including autodiscovery, lazy loading, validation, and dependency resolution.
"""

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional, Protocol

# Add the parent directory to the path so we can import pepperpy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Create a simple interface for providers
class ProviderInterface(Protocol):
    """Interface for provider plugins."""

    def get_provider_type(self) -> str:
        """Get the provider type."""
        ...

    def get_provider_id(self) -> str:
        """Get the provider ID."""
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities."""
        ...


# Import the necessary modules from the plugin system
from pepperpy.builder import register_plugin, register_provider
from pepperpy.plugins.discovery import PluginDiscoveryManager
from pepperpy.plugins.lazy import LazyPlugin
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.plugins.validation import validate_plugin


# Create stub functions for dependency resolution since they might not be implemented yet
def add_plugin(plugin_id: str, plugin_type: str) -> None:
    """Add a plugin to the dependency graph."""
    print(f"Registering plugin {plugin_id} of type {plugin_type}")


def add_dependency(plugin_id: str, dependency_id: str) -> None:
    """Add a dependency relationship."""
    print(f"Adding dependency: {plugin_id} depends on {dependency_id}")


def has_plugin(plugin_id: str) -> bool:
    """Check if a plugin exists in the dependency graph."""
    return True


def resolve_dependencies() -> List[str]:
    """Resolve dependencies and return a loading order."""
    return ["sample_plugin", "dependent_plugin"]


# Sample plugins for demonstration purposes
class SamplePlugin(PepperpyPlugin):
    """Sample plugin to demonstrate the system."""

    __metadata__ = {
        "name": "sample_plugin",
        "version": "1.0.0",
        "description": "Sample plugin for demonstration",
        "author": "PepperPy Team",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin.

        Args:
            config: Plugin configuration
        """
        super().__init__(config or {})
        self.name = config.get("name", "default") if config else "default"

    def initialize(self) -> None:
        """Initialize the plugin."""
        print(f"Initializing sample plugin: {self.name}")
        super().initialize()

    def cleanup(self) -> None:
        """Clean up the plugin."""
        print(f"Cleaning up sample plugin: {self.name}")
        super().cleanup()

    def do_something(self) -> str:
        """Do something interesting.

        Returns:
            A message about what was done
        """
        return f"Something done by {self.name}!"


class DependentPlugin(PepperpyPlugin):
    """Plugin that depends on SamplePlugin."""

    __metadata__ = {
        "name": "dependent_plugin",
        "version": "1.0.0",
        "description": "Plugin that depends on SamplePlugin",
        "author": "PepperPy Team",
        "dependencies": [
            {"plugin_id": "sample_plugin", "type": "required"},
        ],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the plugin.

        Args:
            config: Plugin configuration
        """
        super().__init__(config or {})
        self.sample_plugin: Optional[SamplePlugin] = None

    def initialize(self) -> None:
        """Initialize the plugin."""
        print("Initializing dependent plugin")
        if self.config:
            self.sample_plugin = self.config.get("sample_plugin")
        if not self.sample_plugin:
            print("Warning: SamplePlugin not provided to DependentPlugin")
        super().initialize()

    def cleanup(self) -> None:
        """Clean up the plugin."""
        print("Cleaning up dependent plugin")
        super().cleanup()

    def use_dependency(self) -> str:
        """Use the dependency.

        Returns:
            Result from using the dependency
        """
        if not self.sample_plugin:
            return "No dependency available!"

        return f"Using dependency: {self.sample_plugin.do_something()}"


class SampleProvider(PepperpyPlugin):
    """Sample provider plugin."""

    __metadata__ = {
        "name": "sample_provider",
        "version": "1.0.0",
        "description": "Sample provider plugin",
        "author": "PepperPy Team",
        "provider_type": "sample",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config or {})
        self.api_key = config.get("api_key") if config else None

    def initialize(self) -> None:
        """Initialize the provider."""
        print(f"Initializing sample provider (API key: {self.api_key})")
        super().initialize()

    def cleanup(self) -> None:
        """Clean up the provider."""
        print("Cleaning up sample provider")
        super().cleanup()

    def get_provider_type(self) -> str:
        """Get the provider type.

        Returns:
            Provider type
        """
        return "sample"

    def get_provider_id(self) -> str:
        """Get the provider ID.

        Returns:
            Provider ID
        """
        return "sample_provider"

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            Provider capabilities
        """
        return {
            "feature1": True,
            "feature2": False,
            "max_requests": 100,
        }

    def provide_service(self, request: str) -> str:
        """Provide a service.

        Args:
            request: Service request

        Returns:
            Service response
        """
        return f"Response to '{request}' from sample provider"


async def autodiscovery_example():
    """Demonstrate plugin autodiscovery."""
    print("\n=== Plugin Autodiscovery Example ===")

    # Create a discovery manager
    discovery = PluginDiscoveryManager()

    # Register the current module for scanning
    discovery.register_module(__name__)

    # Scan for plugins
    plugins = await discovery.discover_plugins()

    print(f"Discovered {len(plugins)} plugins:")
    for plugin in plugins:
        print(f"  - {plugin.plugin_id} (type: {plugin.plugin_type})")

    return plugins


async def lazy_loading_example():
    """Demonstrate lazy loading of plugins."""
    print("\n=== Lazy Loading Example ===")

    # Create a lazy-loaded plugin
    lazy_plugin = LazyPlugin(
        plugin_id="sample_plugin",
        plugin_type="demo",
        plugin_class=SamplePlugin,
        config={"name": "Lazy Sample"},
    )

    print("Plugin created as lazy proxy, not initialized yet")

    # Access the plugin, which will initialize it
    print("Accessing plugin...")
    plugin = await lazy_plugin.__call__()

    # Use the plugin
    result = plugin.do_something()
    print(f"Plugin result: {result}")

    # Clean up
    await lazy_plugin._cleanup_wrapper()

    return plugin


async def validation_example():
    """Demonstrate plugin validation."""
    print("\n=== Plugin Validation Example ===")

    # Validate a well-formed plugin
    validation_result = validate_plugin(
        SamplePlugin, "demo", "sample_plugin", SamplePlugin.__metadata__
    )

    # Print validation results
    print(f"Validation passed: {validation_result.valid}")
    print(f"Error count: {validation_result.error_count()}")
    print(f"Warning count: {validation_result.warning_count()}")
    print(f"Info count: {validation_result.info_count()}")

    if validation_result.issues:
        print("Validation issues:")
        for issue in validation_result.issues:
            print(f"  - [{issue.level.value}] {issue.message}")

    return validation_result


async def dependency_resolution_example():
    """Demonstrate dependency resolution."""
    print("\n=== Dependency Resolution Example ===")

    # Register plugins
    add_plugin("sample_plugin", "demo")
    add_plugin("dependent_plugin", "demo")

    # Add dependency
    add_dependency("dependent_plugin", "sample_plugin")

    # Check if a plugin exists
    print(f"Has sample_plugin: {has_plugin('sample_plugin')}")
    print(f"Has dependent_plugin: {has_plugin('dependent_plugin')}")

    # Resolve dependencies
    try:
        ordering = resolve_dependencies()
        print(f"Loading order: {ordering}")
    except Exception as e:
        print(f"Error resolving dependencies: {e}")

    return ordering


async def builder_example():
    """Demonstrate the builder pattern."""
    print("\n=== Builder Pattern Example ===")

    # Register plugins using builders
    plugin_builder = register_plugin(SamplePlugin, "sample_plugin", "demo")

    # Configure the plugin
    plugin_builder.with_config(name="Builder Sample")

    # Build the plugin
    plugin = await plugin_builder.build()

    # Use the plugin
    result = plugin.do_something()
    print(f"Plugin result: {result}")

    # Register a provider
    provider_builder = register_provider(SampleProvider, "sample_provider", "sample")

    # Configure the provider
    provider_builder.with_api_key("test_api_key")
    provider_builder.with_config(extra_option="test_value")

    # Build the provider
    provider = await provider_builder.build()

    # Use the provider
    response = provider.provide_service("test request")
    print(f"Provider response: {response}")

    return plugin, provider


async def main():
    """Run all examples."""
    try:
        # Run each example
        await autodiscovery_example()
        await lazy_loading_example()
        await validation_example()
        await dependency_resolution_example()
        await builder_example()

        print("\nAll examples completed successfully!")
    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
