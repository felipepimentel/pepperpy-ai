#!/usr/bin/env python
"""
Discovery example.

This example shows how to use the discovery system to find and register
plugins, services, and content types.
"""

import asyncio
import sys

from pepperpy.plugin.discovery import PluginDiscoveryProvider


async def main():
    """Run discovery example."""
    # Print explanation
    print("PepperPy Discovery Example")
    print("=========================")
    print("This example shows how to discover plugins and services.")
    print()

    # Create a discovery provider
    discovery_provider = PluginDiscoveryProvider(
        config={
            "scan_paths": [
                "examples/plugins",
            ]
        }
    )

    # Discover plugins
    print("Discovering plugins...")
    plugins = await discovery_provider.discover_plugins()
    print(f"Found {len(plugins)} plugin types")
    print()

    # List all discovered plugins
    print("Available plugins:")
    for plugin in plugins:
        print(
            f"- {plugin.name} ({plugin.plugin_type}.{plugin.provider_type}): {plugin.description}"
        )
    print()

    # Clean up resources
    await discovery_provider.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Example interrupted.")
        sys.exit(0)
