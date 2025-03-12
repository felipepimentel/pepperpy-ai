#!/usr/bin/env python
"""Example demonstrating the plugin system for extensibility.

This example shows how to create, register, and use plugins with the
PepperPy framework's plugin system.

Purpose:
    Demonstrate how to use the plugin system for extensibility in PepperPy.

Requirements:
    - Python 3.9+
    - PepperPy library

Usage:
    1. Install dependencies:
       pip install -e .

    2. Run the example:
       python examples/plugin_system_example.py
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List

# Import directly from the module since the plugins module is new
# and may not be exposed in the public API yet
from pepperpy.core.plugins import (
    Plugin,
    PluginDecorator,
    PluginHook,
    PluginInfo,
    add_plugin_dir,
    call_hooks,
    call_hooks_async,
    disable_plugin,
    enable_plugin,
    get_enabled_plugins,
    get_plugins,
    register_hook,
    register_plugin,
)
from pepperpy.errors import PepperpyError
from pepperpy.utils.logging import get_logger

logger = get_logger(__name__)


class SimplePlugin(Plugin):
    """A simple plugin implementation."""

    def __init__(self, name: str, version: str, description: str):
        """Initialize the plugin.

        Args:
            name: The name of the plugin
            version: The version of the plugin
            description: The description of the plugin
        """
        self._info = PluginInfo(
            name=name,
            version=version,
            description=description,
            author="PepperPy",
            license="MIT",
        )

    @property
    def info(self) -> PluginInfo:
        """Get plugin information.

        Returns:
            Plugin information
        """
        return self._info

    def initialize(self) -> None:
        """Initialize the plugin."""
        print(f"Initializing plugin: {self.info.name}")

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        print(f"Shutting down plugin: {self.info.name}")

    def register_hooks(self) -> Dict[str, List[callable]]:
        """Register hooks for the plugin.

        Returns:
            A dictionary mapping hook names to lists of callables
        """
        return {
            "example_hook": [self.example_hook],
            PluginHook.INITIALIZE.value: [self.on_framework_initialize],
            PluginHook.SHUTDOWN.value: [self.on_framework_shutdown],
        }

    def example_hook(self, message: str) -> str:
        """Example hook implementation.

        Args:
            message: The message to process

        Returns:
            The processed message
        """
        return f"[{self.info.name}] {message}"

    def on_framework_initialize(self) -> None:
        """Handle framework initialization."""
        print(f"Framework initialized (from {self.info.name})")

    def on_framework_shutdown(self) -> None:
        """Handle framework shutdown."""
        print(f"Framework shutdown (from {self.info.name})")


@PluginDecorator(
    name="decorated-plugin",
    version="1.0.0",
    description="A plugin created using the decorator",
    author="PepperPy",
    license="MIT",
    tags=["example", "decorator"],
)
class DecoratedPlugin:
    """A plugin created using the decorator."""

    def __init__(self):
        """Initialize the plugin."""
        self.data = {}

    def on_initialize(self) -> None:
        """Initialize the plugin."""
        print(f"Initializing decorated plugin: {self.info.name}")
        self.data["initialized"] = True

    def on_shutdown(self) -> None:
        """Shutdown the plugin."""
        print(f"Shutting down decorated plugin: {self.info.name}")
        self.data["initialized"] = False

    @property
    def is_initialized(self) -> bool:
        """Check if the plugin is initialized.

        Returns:
            True if the plugin is initialized, False otherwise
        """
        return self.data.get("initialized", False)


def create_plugin_file(plugin_dir: Path) -> Path:
    """Create a plugin file in the plugin directory.

    Args:
        plugin_dir: The plugin directory

    Returns:
        The path to the created plugin file
    """
    # Create the plugin directory if it doesn't exist
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create the plugin package
    package_dir = plugin_dir / "pepperpy_plugin_example"
    package_dir.mkdir(exist_ok=True)

    # Create the __init__.py file
    init_file = package_dir / "__init__.py"
    init_file.write_text(
        """
from pepperpy.core.plugins import Plugin, PluginInfo, register_plugin

class ExamplePlugin(Plugin):
    def __init__(self):
        self._info = PluginInfo(
            name="example-plugin",
            version="1.0.0",
            description="An example plugin",
            author="PepperPy",
            license="MIT",
        )

    @property
    def info(self):
        return self._info

    def initialize(self):
        print(f"Initializing example plugin: {self.info.name}")

    def shutdown(self):
        print(f"Shutting down example plugin: {self.info.name}")

    def register_hooks(self):
        return {
            "example_hook": [self.example_hook],
        }

    def example_hook(self, message):
        return f"[{self.info.name}] {message}"

# Register the plugin
register_plugin(ExamplePlugin())
"""
    )

    return init_file


async def example_basic_plugins():
    """Demonstrate basic plugin usage."""
    print("\n=== Basic Plugin Example ===")

    # Create a simple plugin
    plugin = SimplePlugin(
        name="simple-plugin",
        version="1.0.0",
        description="A simple plugin example",
    )

    # Register the plugin
    register_plugin(plugin)
    print(f"Registered plugin: {plugin.info.name}")

    # Enable the plugin
    enable_plugin(plugin.info.name)
    print(f"Enabled plugin: {plugin.info.name}")

    # Call a hook
    results = call_hooks("example_hook", "Hello, world!")
    for result in results:
        print(f"Hook result: {result}")

    # Disable the plugin
    disable_plugin(plugin.info.name)
    print(f"Disabled plugin: {plugin.info.name}")


async def example_decorated_plugins():
    """Demonstrate decorated plugin usage."""
    print("\n=== Decorated Plugin Example ===")

    # Create a decorated plugin
    plugin = DecoratedPlugin()

    # Register the plugin
    register_plugin(plugin)
    print(f"Registered plugin: {plugin.info.name}")

    # Enable the plugin
    enable_plugin(plugin.info.name)
    print(f"Enabled plugin: {plugin.info.name}")
    print(f"Plugin initialized: {plugin.is_initialized}")

    # Disable the plugin
    disable_plugin(plugin.info.name)
    print(f"Disabled plugin: {plugin.info.name}")
    print(f"Plugin initialized: {plugin.is_initialized}")


async def example_discovered_plugins():
    """Demonstrate plugin discovery."""
    print("\n=== Plugin Discovery Example ===")

    # Create a temporary directory for plugins
    with tempfile.TemporaryDirectory() as temp_dir:
        plugin_dir = Path(temp_dir)
        print(f"Created temporary plugin directory: {plugin_dir}")

        # Create a plugin file
        plugin_file = create_plugin_file(plugin_dir)
        print(f"Created plugin file: {plugin_file}")

        # Add the plugin directory
        add_plugin_dir(plugin_dir)
        print(f"Added plugin directory: {plugin_dir}")

        # Discover plugins
        discovered_plugins = asyncio.create_task(discover_plugins_async(plugin_dir))
        await discovered_plugins


async def discover_plugins_async(plugin_dir: Path):
    """Discover plugins asynchronously.

    Args:
        plugin_dir: The plugin directory
    """
    from pepperpy.core.plugins import discover_plugins

    # Discover plugins
    plugin_names = discover_plugins()
    print(f"Discovered plugins: {plugin_names}")

    # Get all plugins
    plugins = get_plugins()
    for name, plugin in plugins.items():
        print(f"Plugin: {name} (v{plugin.info.version})")

    # Enable all plugins
    for name in plugin_names:
        if name not in get_enabled_plugins():
            enable_plugin(name)
            print(f"Enabled plugin: {name}")

    # Call a hook
    results = call_hooks("example_hook", "Hello from discovered plugin!")
    for result in results:
        print(f"Hook result: {result}")

    # Disable all plugins
    for name in plugin_names:
        if name in get_enabled_plugins():
            disable_plugin(name)
            print(f"Disabled plugin: {name}")


async def example_custom_hooks():
    """Demonstrate custom hooks."""
    print("\n=== Custom Hooks Example ===")

    # Register a custom hook
    def custom_hook(message: str) -> str:
        return f"[Custom Hook] {message}"

    register_hook("custom_hook", custom_hook)
    print("Registered custom hook")

    # Call the custom hook
    results = call_hooks("custom_hook", "Hello from custom hook!")
    for result in results:
        print(f"Hook result: {result}")

    # Register an async custom hook
    async def async_custom_hook(message: str) -> str:
        await asyncio.sleep(0.1)  # Simulate async work
        return f"[Async Custom Hook] {message}"

    register_hook("async_custom_hook", async_custom_hook)
    print("Registered async custom hook")

    # Call the async custom hook
    results = await call_hooks_async(
        "async_custom_hook", "Hello from async custom hook!"
    )
    for result in results:
        print(f"Async hook result: {result}")


async def example_framework_hooks():
    """Demonstrate framework hooks."""
    print("\n=== Framework Hooks Example ===")

    # Create a simple plugin
    plugin = SimplePlugin(
        name="framework-hooks-plugin",
        version="1.0.0",
        description="A plugin for framework hooks",
    )

    # Register and enable the plugin
    register_plugin(plugin)
    enable_plugin(plugin.info.name)

    # Call the initialize hook
    print("Calling initialize hook...")
    call_hooks(PluginHook.INITIALIZE.value)

    # Call the shutdown hook
    print("Calling shutdown hook...")
    call_hooks(PluginHook.SHUTDOWN.value)

    # Disable the plugin
    disable_plugin(plugin.info.name)


async def main():
    """Run all examples."""
    print("Plugin System Example")
    print("====================")

    try:
        # Run the basic plugins example
        await example_basic_plugins()

        # Run the decorated plugins example
        await example_decorated_plugins()

        # Run the discovered plugins example
        await example_discovered_plugins()

        # Run the custom hooks example
        await example_custom_hooks()

        # Run the framework hooks example
        await example_framework_hooks()

    except PepperpyError as e:
        logger.error(f"Error in example: {e}")


if __name__ == "__main__":
    asyncio.run(main())
