"""Example script demonstrating the writer agent's capabilities.

This example shows how to:
1. Write an article on a given topic
2. Edit and improve content
3. Adapt content to different styles
"""

import asyncio
from pathlib import Path

from pepperpy import Pepperpy
from pepperpy.core.base import AgentConfig
from pepperpy.hub.agents.writer import WriterAgent


async def main():
    """Run the writer agent example."""
    # Initialize Pepperpy and create a writer agent
    pepperpy = await Pepperpy.create()
    if not pepperpy._initialized or not pepperpy._client:
        raise RuntimeError("Pepperpy not initialized. Call create() first.")

    config = AgentConfig(
        type="writer",
        name="writer",
        description="Agent specialized in writing and editing content",
        version="0.1.0",
        capabilities=["write", "edit", "adapt", "format"],
    )
    agent = WriterAgent(pepperpy._client, config)
    await agent.initialize()

    try:
        # Example 1: Write an article
        print("\n=== Writing an Article ===")
        result = await agent.write(
            "The Impact of AI on Software Development",
            style="technical",
            format="article",
            tone="positive",
            length="medium",
            outline=[
                "Current state of AI in software development",
                "Key benefits and challenges",
                "Future predictions and trends",
                "Recommendations for developers",
            ],
        )
        print(f"\nTitle: {result['title']}")
        print(f"\nContent:\n{result['content']}")
        print(f"\nSummary: {result['summary']}")
        print(f"\nMetadata: {result['metadata']}")

        # Example 2: Edit and improve content
        print("\n=== Editing Content ===")
        original_content = """
        AI technology is changing how we write software. It helps developers write
        code faster and better. But there are also some problems we need to think
        about. This article will talk about the good and bad things about AI in
        software development.
        """
        edited = await agent.edit(
            original_content,
            focus="clarity and professionalism",
            style="technical",
            improve=["clarity", "structure", "technical_depth"],
        )
        print(f"\nOriginal:\n{original_content}")
        print(f"\nEdited:\n{edited['content']}")
        print("\nChanges made:")
        for change in edited["changes"]:
            print(f"- {change}")
        print("\nSuggestions:")
        for suggestion in edited["suggestions"]:
            print(f"- {suggestion}")

        # Example 3: Adapt content style
        print("\n=== Adapting Content Style ===")
        technical_content = """
        The implementation of machine learning algorithms in software development
        workflows has demonstrated a 43% increase in code completion accuracy and
        a 27% reduction in debugging time across our test cases.
        """
        casual = await agent.adapt(
            technical_content,
            target_style="casual",
            preserve=["key_points", "accuracy"],
        )
        print(f"\nTechnical:\n{technical_content}")
        print(f"\nCasual:\n{casual}")

    finally:
        # Clean up resources
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
