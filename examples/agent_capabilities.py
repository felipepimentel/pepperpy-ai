"""Example demonstrating Pepperpy's agent capabilities.

This example shows how to:
1. Load agents from the Hub
2. Use hot-reload during development
3. Work with teams and monitor progress
4. Handle user intervention
"""

import asyncio
from pathlib import Path
from typing import cast

from pepperpy import Pepperpy
from pepperpy.hub.agents.researcher import ResearcherAgent
from pepperpy.hub.agents.writer import WriterAgent


async def demonstrate_agent_loading() -> None:
    """Demonstrate loading agents with specific capabilities."""
    pepper = await Pepperpy.create()

    # Load researcher with specific capabilities
    researcher = cast(
        ResearcherAgent,
        await pepper.hub.agent(
            "researcher",
            capabilities=["research", "summarize"],
        ),
    )
    result = await researcher.research("Impact of AI")
    if isinstance(result, dict):
        print("\nResearch Result:")
        print(f"Summary: {result.get('summary', 'No summary available')}")
        print(f"Key Points: {result.get('key_points', [])}")
    else:
        print("\nUnexpected research result format")

    # Load writer with configuration
    writer = cast(
        WriterAgent,
        await pepper.hub.agent(
            "writer",
            config={
                "style": "technical",
                "format": "article",
            },
        ),
    )
    article = await writer.write("Future of AI")
    if isinstance(article, dict):
        print("\nGenerated Article:")
        print(f"Title: {article.get('title', 'Untitled')}")
        content = article.get("content", "")
        if content:
            print(f"Content: {content[:200]}...")
        else:
            print("No content available")
    else:
        print("\nUnexpected article format")


async def demonstrate_hot_reload() -> None:
    """Demonstrate hot-reload functionality during development."""
    pepper = await Pepperpy.create()

    # Create a local agent configuration
    agent_dir = Path.home() / ".pepper_hub" / "hub" / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)

    agent_config = {
        "name": "custom-writer",
        "base": "writer",
        "config": {
            "style": "technical",
            "format": "article",
        },
    }

    config_path = agent_dir / "custom-writer.yaml"
    with open(config_path, "w") as f:
        import yaml

        yaml.dump(agent_config, f)

    # Use hot-reload to automatically update when config changes
    @pepper.hub.watch("agents/custom-writer.yaml")
    async def use_writer():
        writer = cast(WriterAgent, await pepper.hub.agent("custom-writer"))
        result = await writer.write("AI Technology")
        if isinstance(result, dict):
            print("\nWriter Output:")
            print(f"Title: {result.get('title', 'Untitled')}")
            content = result.get("content", "")
            if content:
                print(f"Content: {content[:200]}...")
            else:
                print("No content available")
        else:
            print("\nUnexpected output format")

    # Run the function (it will auto-reload when config changes)
    await use_writer()

    # Simulate config change
    agent_config["config"]["style"] = "casual"
    with open(config_path, "w") as f:
        yaml.dump(agent_config, f)

    # Wait for hot-reload
    await asyncio.sleep(1)
    await use_writer()


async def demonstrate_team_monitoring() -> None:
    """Demonstrate team execution with monitoring."""
    pepper = await Pepperpy.create()

    # Load pre-configured team
    team = await pepper.hub.team("research-team")

    print("\nStarting team execution...")
    async with team.run("Write an article about AI trends") as session:
        while session.progress.progress < 100 and not session.needs_input:
            print(f"\nCurrent Step: {session.current_step}")
            print(f"Progress: {session.progress.progress:.1f}%")
            print(f"Active Agents: {session.progress.active_agents}")

            if session.thoughts:
                print("\nThoughts:")
                for thought in session.thoughts[-3:]:  # Show last 3 thoughts
                    print(f"- {thought}")

            if session.needs_input:
                print("\nTeam needs input!")
                session.provide_input("Focus on machine learning applications")

            await asyncio.sleep(1)  # Check progress every second

    print("\nTeam execution completed!")


async def main() -> None:
    """Run the examples."""
    print("\n1. Agent Loading Example:")
    print("-" * 50)
    await demonstrate_agent_loading()

    print("\n2. Hot-Reload Example:")
    print("-" * 50)
    await demonstrate_hot_reload()

    print("\n3. Team Monitoring Example:")
    print("-" * 50)
    await demonstrate_team_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
