"""Example demonstrating Pepperpy Hub integration features.

This example shows how to:
1. Create and manage local components
2. Share and discover components
3. Use hot-reload during development
4. Create custom agent templates
"""

import asyncio
from pathlib import Path
from typing import cast

import yaml

from pepperpy import Pepperpy
from pepperpy.hub.agents.researcher import ResearcherAgent


async def demonstrate_component_management() -> None:
    """Demonstrate creating and managing local components."""
    pepper = await Pepperpy.create()

    # Create a custom agent
    agent = cast(
        ResearcherAgent,
        await pepper.hub.create_agent(
            name="custom-researcher",
            base="researcher",
            config={
                "style": "technical",
                "depth": "comprehensive",
            },
            capabilities=["research", "summarize", "analyze"],
        ),
    )

    # Use the agent
    result = await agent.research("Latest AI developments")
    print("\nCustom Agent Result:")
    print(f"Depth: {result.get('depth', 'N/A')}")
    print(f"Analysis: {result.get('analysis', 'N/A')}")

    # List available components
    components = await pepper.hub.list_shared_components("agent")
    print("\nAvailable Agents:")
    for comp in components:
        print(f"- {comp['name']} (v{comp['metadata'].get('version', '0.1.0')})")
        print(f"  Tags: {', '.join(comp['metadata'].get('tags', []))}")


async def demonstrate_component_sharing() -> None:
    """Demonstrate sharing and discovering components."""
    pepper = await Pepperpy.create()

    # Create a shareable agent
    await pepper.hub.create_agent(
        name="technical-writer",
        base="writer",
        config={
            "style": "technical",
            "format": "documentation",
            "metadata": {
                "author": "Your Name",
                "version": "1.0.0",
                "tags": ["technical", "documentation"],
                "description": "Specialized writer for technical documentation",
            },
        },
    )

    # Publish the agent
    await pepper.hub.publish("technical-writer")

    # Get component info
    info = await pepper.hub.get_component_info("technical-writer")
    print("\nPublished Component Info:")
    print(f"Name: {info['name']}")
    print(f"Version: {info['metadata']['version']}")
    print(f"Description: {info['metadata']['description']}")


async def demonstrate_development_workflow() -> None:
    """Demonstrate development workflow with hot-reload."""
    pepper = await Pepperpy.create()

    # Create a development agent
    agent_config = {
        "name": "dev-agent",
        "base": "researcher",
        "config": {
            "style": "experimental",
            "capabilities": ["research", "experiment"],
        },
    }

    # Save config
    config_dir = Path.home() / ".pepper_hub" / "hub" / "agents"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "dev-agent.yaml"

    with open(config_path, "w") as f:
        yaml.dump(agent_config, f)

    # Use hot-reload for development
    @pepper.hub.watch("agents/dev-agent.yaml")
    async def develop_agent():
        agent = cast(ResearcherAgent, await pepper.hub.agent("dev-agent"))
        result = await agent.research("Experimental AI techniques")
        print("\nDevelopment Result:")
        print(f"Style: {result.get('style', 'N/A')}")
        print(f"Findings: {result.get('findings', 'N/A')}")

    # Initial run
    await develop_agent()

    # Modify config during development
    agent_config["config"]["style"] = "cutting-edge"
    with open(config_path, "w") as f:
        yaml.dump(agent_config, f)

    # Wait for hot-reload
    await asyncio.sleep(1)
    await develop_agent()


async def demonstrate_custom_templates() -> None:
    """Demonstrate creating and using custom agent templates."""
    pepper = await Pepperpy.create()

    # Create template directory
    template_dir = Path.home() / ".pepper_hub" / "hub" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)

    # Define a custom template
    template_config = {
        "name": "specialized-researcher",
        "base": "researcher",
        "config": {
            "style": "academic",
            "depth": "deep",
            "citation_style": "apa",
        },
        "metadata": {
            "type": "template",
            "description": "Template for academic research agents",
            "version": "1.0.0",
        },
    }

    # Save template
    template_path = template_dir / "specialized-researcher.yaml"
    with open(template_path, "w") as f:
        yaml.dump(template_config, f)

    # Create agent from template
    agent = cast(
        ResearcherAgent,
        await pepper.hub.create_agent(
            name="ai-researcher",
            base="specialized-researcher",
            config={"field": "artificial-intelligence"},
        ),
    )

    # Use the specialized agent
    result = await agent.research("Neural architecture search")
    print("\nSpecialized Research Result:")
    print(f"Style: {result.get('style', 'N/A')}")
    print(f"Citations: {result.get('citations', [])}")


async def main() -> None:
    """Run the examples."""
    print("\n1. Component Management Example:")
    print("-" * 50)
    await demonstrate_component_management()

    print("\n2. Component Sharing Example:")
    print("-" * 50)
    await demonstrate_component_sharing()

    print("\n3. Development Workflow Example:")
    print("-" * 50)
    await demonstrate_development_workflow()

    print("\n4. Custom Templates Example:")
    print("-" * 50)
    await demonstrate_custom_templates()


if __name__ == "__main__":
    asyncio.run(main())
