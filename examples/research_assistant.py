"""Example of using the research assistant agent."""

import asyncio
import os
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from pydantic import SecretStr

from pepperpy.hub import Hub
from pepperpy.hub.agents.base import AgentConfig
from pepperpy.hub.agents.research_assistant import ResearchAssistantAgent
from pepperpy.monitoring import logger
from pepperpy.providers import get_provider
from pepperpy.providers.base import Provider, ProviderConfig

# Load environment variables
load_dotenv()

# Configure the hub to use the local .pepper_hub directory
hub = Hub(storage_dir=Path(__file__).parent.parent / ".pepper_hub")

log = logger.bind(example="research_assistant")


async def main():
    """Run the research assistant example."""
    # Load the research assistant configuration
    raw_config = hub.load_artifact("agents", "research_assistant")

    # Create provider config
    provider_config = ProviderConfig(
        provider_type=os.getenv("PEPPERPY_PROVIDER", "openrouter"),
        model=os.getenv("PEPPERPY_MODEL", "openai/gpt-4o-mini"),
        temperature=float(os.getenv("PEPPERPY_AGENT__TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("PEPPERPY_AGENT__MAX_TOKENS", "1000")),
        api_key=SecretStr(os.getenv("PEPPERPY_API_KEY", "")),
    )

    # Get provider instance
    provider = get_provider(provider_config.provider_type, provider_config)

    async with provider as initialized_provider:
        try:
            # Create agent config with initialized provider
            config = AgentConfig(
                provider=cast(Provider, initialized_provider),
                parameters=raw_config,
            )

            # Create the research assistant agent
            agent = ResearchAssistantAgent(config)

            # Run the agent with a research topic
            topic = "Large Language Models and their impact on scientific research"

            log.info(
                "Starting research assistant",
                topic=topic,
                model=provider_config.model,
                provider=provider_config.provider_type,
            )

            # First, analyze the topic
            analysis = await agent.analyze_topic(topic=topic)
            print("\nTopic Analysis:")
            print("=" * 80)
            print(analysis)
            print("=" * 80)

            # Then, find relevant sources
            sources = await agent.find_sources(topic=topic, max_sources=5)
            print("\nRelevant Sources:")
            print("=" * 80)
            print(sources)
            print("=" * 80)

            # Finally, analyze the sources
            if sources:
                synthesis = await agent.analyze_sources(sources=sources)
                print("\nSource Analysis and Synthesis:")
                print("=" * 80)
                print(synthesis)
                print("=" * 80)

        finally:
            # Cleanup agent
            await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
