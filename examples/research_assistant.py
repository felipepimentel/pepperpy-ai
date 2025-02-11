"""Example of using the research assistant agent."""

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from pepperpy.agents.research_assistant import ResearchAssistant
from pepperpy.hub import Hub
from pepperpy.monitoring import logger

# Load environment variables
load_dotenv()

# Configure the hub to use the local .pepper_hub directory
hub = Hub(storage_dir=Path(__file__).parent.parent / ".pepper_hub")

log = logger.bind(example="research_assistant")


async def main():
    """Run the research assistant example."""
    # Load the research assistant configuration
    config = hub.load_artifact("agents", "research_assistant")

    # Create the research assistant agent
    agent = ResearchAssistant(config)

    # Run the agent with a research topic
    topic = "Large Language Models and their impact on scientific research"

    log.info("Starting research assistant", topic=topic)

    response = await agent.run(topic=topic)

    print("\nResearch Assistant Response:")
    print("=" * 80)
    print(response)
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
