"""Example demonstrating the Content Generator Workflow plugin.

This example shows how to use the Content Generator Workflow plugin
to generate content on a specific topic with automatic research,
outlining, and refinement.
"""

import asyncio
import os
from pathlib import Path

from pepperpy.plugins import PluginManager

# Setup paths
EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def main() -> None:
    """Run the example."""
    print("Content Generator Workflow Example")
    print("=" * 50)

    # Create and initialize the workflow provider
    workflow = PluginManager.create_provider(
        "workflow", "content_generator", style="conversational"
    )
    await workflow.initialize()

    # Generate content on a specific topic
    print("\nGenerating content on 'Artificial Intelligence'...")
    result = await workflow.generate_content("Artificial Intelligence")

    # Print the generated content
    print(f"\nGenerated content for '{result['title']}':")
    print("-" * 50)
    print(result["content"])
    print("-" * 50)

    # Output to file
    output_file = OUTPUT_DIR / "ai_content.md"
    with open(output_file, "w") as f:
        f.write(result["content"])
    print(f"\nContent saved to: {output_file}")

    # Try with different options
    print("\nGenerating content with different options...")
    advanced_result = await workflow.execute({
        "topic": "Machine Learning Ethics",
        "options": {
            "outline_type": "blog_post",
            "style": "informative",
            "model": "gpt-4",
        },
    })

    # Output to file
    output_file = OUTPUT_DIR / "ml_ethics_content.md"
    with open(output_file, "w") as f:
        f.write(advanced_result["content"])
    print(f"\nAdvanced content saved to: {output_file}")

    # Clean up
    await workflow.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
