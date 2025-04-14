#!/usr/bin/env python3
"""Research Assistant Workflow Demo.

This script demonstrates how to use the Research Assistant workflow
to automate the research process using real LLM and search services.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from plugins.workflow.research_assistant.provider import ResearchAssistantAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("research_demo")


async def run_research(topic: str, **kwargs: Any) -> dict[str, Any]:
    """Run a research task using real services.

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
    """Run the demo with real research capabilities."""
    if len(sys.argv) < 2:
        print(
            "Usage: python run_research_demo.py <topic> [--format FORMAT] [--max-sources COUNT] [--model MODEL] [--api-key KEY]"
        )
        print(
            "Example: python run_research_demo.py 'artificial intelligence' --format markdown --max-sources 3 --model gpt-4"
        )
        sys.exit(1)

    # Parse command line arguments
    topic = sys.argv[1]
    format_type = "markdown"
    max_sources = 5
    model = "gpt-3.5-turbo"
    api_key = os.environ.get("OPENAI_API_KEY")  # Default from environment

    for i, arg in enumerate(sys.argv):
        if arg == "--format" and i + 1 < len(sys.argv):
            format_type = sys.argv[i + 1]
        elif arg == "--max-sources" and i + 1 < len(sys.argv):
            max_sources = int(sys.argv[i + 1])
        elif arg == "--model" and i + 1 < len(sys.argv):
            model = sys.argv[i + 1]
        elif arg == "--api-key" and i + 1 < len(sys.argv):
            api_key = sys.argv[i + 1]

    # Check for API key
    if not api_key and ("gpt" in model or "claude" in model):
        print("Warning: No API key provided. Set with --api-key or OPENAI_API_KEY environment variable.")
        if "gpt" in model:
            print("Hint: You can get an OpenAI API key at https://platform.openai.com/api-keys")
        elif "claude" in model:
            print("Hint: You can get an Anthropic API key at https://console.anthropic.com/")

    # Run the research
    logger.info(f"Starting research on topic: {topic} using model {model}")
    result = await run_research(
        topic=topic,
        report_format=format_type,
        max_sources=max_sources,
        model_id=model,
        api_key=api_key,
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
                
            if "quality_rating" in research["review"]:
                print(f"\nQuality rating: {research['review']['quality_rating']:.2f}/1.00")
    else:
        print(f"Research failed: {result.get('message', 'Unknown error')}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
