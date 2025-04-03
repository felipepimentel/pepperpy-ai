#!/usr/bin/env python3
"""
Improved Plugin System Example.

This example demonstrates improvements to the PepperPy plugin system.
"""

import asyncio
import os
import sys
from typing import Any, Dict, Optional, Protocol

# Add the parent directory to the path so we can import pepperpy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from PepperPy
from pepperpy.plugins.plugin import PepperpyPlugin


class ProviderInterface(Protocol):
    """Interface for provider plugins."""

    def get_provider_type(self) -> str:
        """Get the type of the provider."""
        ...

    def get_provider_id(self) -> str:
        """Get the unique ID of the provider."""
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of the provider."""
        ...


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
        super().__init__(config)
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
        super().__init__(config)
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


class PluginBuilder:
    """Builder pattern for plugins."""

    def __init__(self, plugin_class):
        """Initialize the builder.

        Args:
            plugin_class: Class of the plugin to build
        """
        self.plugin_class = plugin_class
        self.config = {}

    def with_name(self, name: str) -> "PluginBuilder":
        """Set the name of the plugin.

        Args:
            name: Plugin name

        Returns:
            Self for chaining
        """
        self.config["name"] = name
        return self

    def with_api_key(self, api_key: str) -> "PluginBuilder":
        """Set the API key for the plugin.

        Args:
            api_key: API key

        Returns:
            Self for chaining
        """
        self.config["api_key"] = api_key
        return self

    def with_option(self, key: str, value: Any) -> "PluginBuilder":
        """Set an arbitrary option.

        Args:
            key: Option key
            value: Option value

        Returns:
            Self for chaining
        """
        self.config[key] = value
        return self

    def build(self) -> PepperpyPlugin:
        """Build and initialize the plugin.

        Returns:
            Initialized plugin instance
        """
        instance = self.plugin_class(config=self.config)
        instance.initialize()
        return instance


async def basic_plugin_example():
    """Basic example of creating and using a plugin."""
    print("\n=== Basic Plugin Example ===")

    # Create and initialize a plugin
    plugin = SamplePlugin(config={"name": "Test Plugin"})
    plugin.initialize()

    # Use the plugin
    result = plugin.do_something()
    print(f"Plugin result: {result}")

    # Clean up
    plugin.cleanup()

    return plugin


async def provider_example():
    """Example of creating and using a provider plugin."""
    print("\n=== Provider Plugin Example ===")

    # Create and initialize a provider
    provider = SampleProvider(config={"api_key": "test_key_123"})
    provider.initialize()

    # Use the provider
    capabilities = provider.get_capabilities()
    print(f"Provider capabilities: {capabilities}")

    service_result = provider.provide_service("test request")
    print(f"Service result: {service_result}")

    # Clean up
    provider.cleanup()

    return provider


async def builder_example():
    """Example of using the builder pattern."""
    print("\n=== Builder Pattern Example ===")

    # Create a plugin using the builder
    plugin_builder = PluginBuilder(SamplePlugin)
    plugin = plugin_builder.with_name("Builder-created Plugin").build()

    # Use the plugin
    result = plugin.do_something()
    print(f"Plugin result: {result}")

    # Create a provider using the builder
    provider_builder = PluginBuilder(SampleProvider)
    provider = (
        provider_builder.with_api_key("builder_api_key")
        .with_option("timeout", 30)
        .build()
    )

    # Use the provider
    service_result = provider.provide_service("builder request")
    print(f"Service result: {service_result}")

    # Clean up
    plugin.cleanup()
    provider.cleanup()

    return plugin, provider


async def main():
    """Run all examples."""
    try:
        # Run the examples
        await basic_plugin_example()
        await provider_example()
        await builder_example()

        print("\nAll examples completed successfully!")
    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
