#!/usr/bin/env python3
"""Research Assistant Workflow Demo.

This script demonstrates how to use the Research Assistant workflow
to automate the research process.
"""

import asyncio
import json
import logging
import sys
from typing import Any

from provider import ResearchAssistantAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("research_demo")


async def run_research(topic: str, **kwargs: Any) -> dict[str, Any]:
    """Run a research task.

    Args:
        topic: Research topic
        **kwargs: Additional configuration parameters

    Returns:
        Research result
    """
    # Create and initialize the adapter
    adapter = ResearchAssistantAdapter(**kwargs)
    await adapter.initialize()

    try:
        # Execute research task
        result = await adapter.execute({
            "task": "research",
            "topic": topic,
        })

        # If successful, get the complete result
        if result["status"] == "success" and "research_id" in result:
            research_id = result["research_id"]
            complete_result = await adapter.execute({
                "task": "get_result",
                "research_id": research_id,
            })
            return complete_result

        return result
    finally:
        # Clean up resources
        await adapter.cleanup()


async def main() -> None:
    """Run the demo."""
    if len(sys.argv) < 2:
        print(
            "Usage: python run_research_demo.py <topic> [--format FORMAT] [--max-sources COUNT]"
        )
        print(
            "Example: python run_research_demo.py 'artificial intelligence' --format markdown --max-sources 3"
        )
        sys.exit(1)

    # Parse command line arguments
    topic = sys.argv[1]
    format_type = "markdown"
    max_sources = 5

    for i, arg in enumerate(sys.argv):
        if arg == "--format" and i + 1 < len(sys.argv):
            format_type = sys.argv[i + 1]
        elif arg == "--max-sources" and i + 1 < len(sys.argv):
            max_sources = int(sys.argv[i + 1])

    # Run the research
    logger.info(f"Starting research on topic: {topic}")
    result = await run_research(
        topic=topic,
        report_format=format_type,
        max_sources=max_sources,
    )

    # Print the result
    if result["status"] == "success" and "research" in result:
        research = result["research"]
        print("\n" + "=" * 80)
        print(f"Research on '{research['topic']}' completed successfully!")
        print("=" * 80)

        # Print report
        print("\nRESEARCH REPORT:\n")
        print(research["report"])

        # Print review if available
        if research.get("review"):
            print("\nREVIEW FEEDBACK:\n")
            for strength in research["review"]["feedback"]["strengths"]:
                print(f"✓ {strength}")

            print("\nSuggestions for improvement:")
            for suggestion in research["review"]["suggestions"]:
                print(f"• {suggestion}")
    else:
        print(f"Research failed: {result.get('message', 'Unknown error')}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
