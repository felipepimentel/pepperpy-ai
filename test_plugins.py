#!/usr/bin/env python3

import asyncio

from pepperpy.plugin.discovery import PluginDiscoveryProvider
from pepperpy.plugin.registry import plugin_registry
from plugins.workflow.repository_analyzer.provider import RepositoryAnalyzerAdapter


async def main():
    # Initialize plugin discovery
    discovery = PluginDiscoveryProvider()
    # Discover plugins
    await discovery.discover_plugins()

    # Print all registered plugins
    print("Registered plugins:")
    plugins = plugin_registry.list_plugins()
    for domain, domain_plugins in plugins.items():
        print(f"Domain: {domain}")
        for name, plugin_meta in domain_plugins.items():
            cls = plugin_meta.get("class")
            class_name = cls.__name__ if cls and hasattr(cls, "__name__") else "Unknown"
            print(f"  - {name}: {class_name}")

    # Print workflow plugins specifically
    print("\nWorkflow plugins before fix:")
    workflow_plugins = plugin_registry._plugins.get("workflow", {})
    for name, plugin_info in workflow_plugins.items():
        cls = plugin_info.get("class")
        class_name = cls.__name__ if cls and hasattr(cls, "__name__") else "Unknown"
        print(f"  - {name}: {class_name}")

    # Fix the repository_analyzer plugin registration
    print("\nFixing repository_analyzer plugin registration")
    plugin_registry._plugins["workflow"]["repository_analyzer"] = {
        "class": RepositoryAnalyzerAdapter,
        "meta": {},
    }

    # Print workflow plugins after fix
    print("\nWorkflow plugins after fix:")
    workflow_plugins = plugin_registry._plugins.get("workflow", {})
    for name, plugin_info in workflow_plugins.items():
        cls = plugin_info.get("class")
        class_name = cls.__name__ if cls and hasattr(cls, "__name__") else "Unknown"
        print(f"  - {name}: {class_name}")

    # Run a CLI-like command
    print("\nTrying to create workflow provider: repository_analyzer")
    from pepperpy.plugin import create_provider_instance

    try:
        workflow_provider = create_provider_instance("workflow", "repository_analyzer")
        print(f"Successfully created provider: {workflow_provider.__class__.__name__}")

        # Initialize, execute and cleanup
        await workflow_provider.initialize()

        result = await workflow_provider.execute({
            "task": "analyze_structure",
            "repository_path": ".",
            "topic": "repository analysis",
        })

        print("\nExecution result:", result.get("status", "unknown"))

        await workflow_provider.cleanup()
    except Exception as e:
        print(f"Error creating provider: {e}")


if __name__ == "__main__":
    asyncio.run(main())
