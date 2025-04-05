#!/usr/bin/env python
"""
Discovery example.

This example shows how to use the discovery system to find and register
plugins, services, and content types.
"""

import asyncio
import sys

from pepperpy.plugins.providers.discovery.plugin_discovery import (
    PluginDiscoveryProvider,
)


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

    # Initialize the provider
    await discovery_provider.initialize()

    # Discover plugins
    print("Discovering plugins...")
    plugins = await discovery_provider.discover_plugins()
    print(f"Found {len(plugins)} plugin types")
    print()

    # List plugins
    all_plugins = await discovery_provider.list_plugins()
    print("Available plugins:")
    for plugin_info in all_plugins:
        print(
            f"- {plugin_info['name']} ({plugin_info['type']}.{plugin_info['provider']}): {plugin_info['description']}"
        )
    print()

    # Discover services
    print("Discovering services...")
    services = await discovery_provider.discover_services()
    print(f"Found {len(services)} services")
    print()

    # List services
    print("Available services:")
    for service in services:
        print(f"- {service['name']} ({service['id']}): {service['description']}")
    print()

    # Get service info
    if services:
        first_service = services[0]
        service_id = first_service["id"]
        print(f"Getting details for service {service_id}...")
        service_info = await discovery_provider.get_service_info(service_id)
        if service_info:
            print("Service details:")
            for key, value in service_info.items():
                print(f"  {key}: {value}")
        else:
            print(f"Service {service_id} not found")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Example interrupted.")
        sys.exit(0)
