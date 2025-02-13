"""Example demonstrating component sharing and publishing.

This example shows how to:
1. Create and publish custom components
2. List available shared components
3. Get component information
4. Use shared components
"""

import asyncio

from pepperpy import Pepperpy


async def create_and_publish():
    """Create and publish a custom agent."""
    pepper = await Pepperpy.create()

    # Create a custom agent
    agent = await pepper.hub.create_agent(
        "custom-researcher",
        base="researcher",
        capabilities=["research", "analyze", "summarize"],
        config={
            "style": "technical",
            "depth": "comprehensive",
        },
    )

    # Use the agent
    result = await agent.analyze(
        "Impact of AI on Software Development",
        depth="comprehensive",
    )
    print(f"\nResearch Result:\n{result}")

    # Publish the agent
    await pepper.hub.publish("custom-researcher")
    print("\nAgent published successfully!")


async def list_components():
    """List available shared components."""
    pepper = await Pepperpy.create()

    # List all components
    print("\nAll Shared Components:")
    components = await pepper.hub.list_shared_components()
    for comp in components:
        print(f"\n{comp['type'].title()}: {comp['name']}")
        print(f"Version: {comp['metadata']['version']}")
        print(f"Author: {comp['metadata']['author']}")
        print(f"Tags: {', '.join(comp['metadata']['tags'])}")

    # List agents only
    print("\nShared Agents:")
    agents = await pepper.hub.list_shared_components("agent")
    for agent in agents:
        print(f"- {agent['name']} (v{agent['metadata']['version']})")


async def get_component_details():
    """Get detailed information about a component."""
    pepper = await Pepperpy.create()

    # Get agent info
    info = await pepper.hub.get_component_info("custom-researcher")
    print("\nCustom Researcher Details:")
    print(f"Name: {info['name']}")
    print(f"Version: {info['metadata']['version']}")
    print(f"Description: {info['metadata']['description']}")
    print(f"Author: {info['metadata']['author']}")
    print(f"Tags: {', '.join(info['metadata']['tags'])}")


async def use_shared_component():
    """Use a shared component."""
    pepper = await Pepperpy.create()

    # Load and use the shared agent
    agent = await pepper.hub.agent("custom-researcher")
    result = await agent.analyze(
        "Future of AI",
        depth="comprehensive",
        style="technical",
    )
    print(f"\nResearch Result:\n{result}")


async def main():
    """Run the sharing examples."""
    try:
        # Create and publish a component
        await create_and_publish()

        # List available components
        await list_components()

        # Get component details
        await get_component_details()

        # Use a shared component
        await use_shared_component()

    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
