"""Example demonstrating hot-reloading of hub components.

This example shows how to:
1. Watch agent configurations for changes
2. Watch workflow configurations for changes
3. Watch team configurations for changes
4. Use the @watch_component decorator
"""

import asyncio

from pepperpy import Pepperpy
from pepperpy.hub.watcher import ComponentWatcher, watch_component


@watch_component("agents/writer.yaml")
async def use_writer(hub):
    """Use the writer agent with hot-reload support."""
    writer = await hub.agent("writer")
    result = await writer.write(
        "The Future of AI",
        style="technical",
        format="article",
    )
    print(f"\nWriter Result:\n{result}")


async def watch_research_team(hub):
    """Watch and use the research team configuration."""
    watcher = ComponentWatcher()

    async def on_team_update(config):
        """Handle team configuration updates."""
        print(f"\nTeam config updated: {config['name']}")
        team = await hub.team("research-team")
        result = await team.run("Impact of AI on Healthcare")
        print(f"\nTeam Result:\n{result}")

    # Start watching the team configuration
    await watcher.watch_team("research-team", on_team_update)

    try:
        # Keep running to watch for changes
        while True:
            await asyncio.sleep(1)
    finally:
        await watcher.stop()


async def main():
    """Run the hot-reload examples."""
    pepper = await Pepperpy.create()

    print("\nStarting hot-reload example...")
    print("Try modifying the following files to see hot-reload in action:")
    print("- .pepper_hub/hub/agents/writer.yaml")
    print("- .pepper_hub/hub/teams/research-team.yaml")

    # Example 1: Using @watch_component decorator
    print("\nRunning writer example with @watch_component...")
    await use_writer(pepper.hub)

    # Example 2: Using ComponentWatcher
    print("\nWatching research team configuration...")
    print("(Press Ctrl+C to exit)")
    try:
        await watch_research_team(pepper.hub)
    except KeyboardInterrupt:
        print("\nStopping watcher...")


if __name__ == "__main__":
    asyncio.run(main())
