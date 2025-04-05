#!/usr/bin/env python
"""
Simple Plugin Discovery Example.

This example demonstrates how to discover plugins using the framework's API.
"""

import asyncio
import sys
from pathlib import Path

from pepperpy import PepperPy


async def main():
    """Run the simple discovery example."""
    print("PepperPy Simple Discovery Example")
    print("=================================")

    # Setup plugin paths
    plugin_paths = [
        str(Path.cwd() / "plugins"),
    ]

    # Create PepperPy instance with discovery options
    pepperpy = PepperPy(config={"plugin": {"discovery": {"scan_paths": plugin_paths}}})

    # Initialize the framework
    await pepperpy.initialize()

    # List available plugin types
    print("\nAvailable Plugin Types:")
    plugin_types = []

    try:
        from pepperpy.plugin.registry import plugin_registry

        plugins = plugin_registry.list_plugins()

        for domain, providers in plugins.items():
            if not providers:
                continue

            plugin_types.append(domain)
            print(f"- {domain}: {len(providers)} providers")

            for provider_name in providers.keys():
                print(f"  - {provider_name}")
    except Exception as e:
        print(f"Error listing plugins: {e}")

    # Create providers for discovered types
    if plugin_types:
        print("\nTesting Plugin Creation:")

        # Try to create a provider of each type
        for plugin_type in plugin_types:
            try:
                providers = plugins.get(plugin_type, {})
                if not providers:
                    continue

                # Get the first provider
                provider_name = next(iter(providers.keys()))

                print(f"- Creating {plugin_type}/{provider_name} provider...")

                # Create a provider instance
                provider_class = plugin_registry.get_plugin(plugin_type, provider_name)
                if provider_class:
                    provider = provider_class()
                    print(f"  Success! Provider class: {provider.__class__.__name__}")
                else:
                    print("  Failed: No provider class found")

            except Exception as e:
                print(f"  Error: {e}")

    print("\nExample complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted.")
        sys.exit(0)
