"""Example demonstrating the research assistant agent capabilities using the simplified Pepperpy structure.

This example shows how to use the research assistant agent with the new unified configuration
and initialization system to analyze research topics, find relevant sources, and synthesize information.
"""

import asyncio

from pepperpy import PepperpyClient, PepperpyConfig
from pepperpy.monitoring import logger

log = logger.bind(example="research_assistant")


async def main() -> None:
    """Run the research assistant example using the simplified Pepperpy structure."""
    # Load configuration from environment variables
    config = PepperpyConfig.from_env()

    # Use context manager for proper lifecycle management
    async with PepperpyClient(config=config) as client:
        # Get the latest version of the research assistant agent
        agent = await client.get_agent("research_assistant")

        # Define the research topic
        topic = "Large Language Models and their impact on scientific research"

        # Run the research workflow using the simplified high-level API
        outputs = await agent.research(
            topic=topic,
            max_sources=5,
            report_progress=True,  # Enable built-in progress reporting
        )

        # Log workflow completion
        log.info(
            "Research workflow completed",
            outputs=list(outputs.keys()),
        )


if __name__ == "__main__":
    asyncio.run(main())
