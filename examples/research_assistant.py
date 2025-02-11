"""Example demonstrating the research assistant agent capabilities.

This example shows how to use the research assistant agent from the PepperHub
to analyze research topics, find relevant sources, and synthesize information.
It uses the research workflow defined in the hub to orchestrate the process.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, cast

from dotenv import load_dotenv
from pydantic import SecretStr

from pepperpy.hub import Hub
from pepperpy.hub.agents.base import AgentConfig
from pepperpy.hub.agents.research_assistant import ResearchAssistantAgent
from pepperpy.hub.workflows import Workflow, WorkflowConfig
from pepperpy.monitoring import logger
from pepperpy.providers import get_provider
from pepperpy.providers.base import Provider, ProviderConfig

# Load environment variables
load_dotenv()

# Configure the hub to use the local .pepper_hub directory
hub = Hub(storage_dir=Path(__file__).parent.parent / ".pepper_hub")

log = logger.bind(example="research_assistant")


async def setup_workflow() -> Dict[str, Any]:
    """Set up the research workflow configuration.

    Returns
    -------
        Dict[str, Any]: The workflow configuration loaded from the hub.

    """
    # Load workflow configuration
    workflow_config = hub.load_artifact("workflows", "research")

    # Load prompts
    prompts = hub.load_artifact("prompts", "research")

    return {
        "workflow": workflow_config,
        "prompts": prompts,
    }


async def setup_agent() -> ResearchAssistantAgent:
    """Set up and initialize the research assistant agent.

    Returns
    -------
        ResearchAssistantAgent: The configured research assistant agent.

    """
    # Load the research assistant configuration from the hub
    raw_config = hub.load_artifact("agents", "research_assistant")

    # Create provider config from environment variables
    provider_config = ProviderConfig(
        provider_type=os.getenv("PEPPERPY_PROVIDER", "openrouter"),
        model=os.getenv("PEPPERPY_MODEL", "openai/gpt-4o-mini"),
        temperature=float(os.getenv("PEPPERPY_AGENT__TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("PEPPERPY_AGENT__MAX_TOKENS", "1000")),
        api_key=SecretStr(os.getenv("PEPPERPY_API_KEY", "")),
    )

    # Initialize the provider
    provider = get_provider(provider_config.provider_type, provider_config)

    # Create agent config with initialized provider
    config = AgentConfig(
        provider=cast(Provider, provider),
        parameters=raw_config,
    )

    # Create and return the research assistant agent
    return ResearchAssistantAgent(config)


async def run_research_workflow(
    agent: ResearchAssistantAgent,
    workflow_config: Dict[str, Any],
    topic: str,
    max_sources: int = 5,
) -> Dict[str, Any]:
    """Run the research workflow using the research assistant agent.

    Args:
    ----
        agent: The configured research assistant agent.
        workflow_config: The workflow configuration from the hub.
        topic: The research topic to analyze.
        max_sources: Maximum number of sources to find.

    Returns:
    -------
        Dict[str, Any]: The results of the workflow execution.

    """
    log.info(
        "Starting research workflow",
        topic=topic,
        max_sources=max_sources,
    )

    # Create workflow configuration
    config = WorkflowConfig(
        name="research",
        description="Research workflow execution",
        steps=workflow_config["workflow"]["steps"],
        inputs=workflow_config["workflow"]["inputs"],
        outputs=workflow_config["workflow"]["outputs"],
    )

    # Create workflow instance
    workflow = Workflow(config)

    # Execute workflow steps
    outputs = {}

    # Step 1: Initial research
    log.info("Performing initial research...")
    analysis = await agent.analyze_topic(topic=topic)
    outputs["summary"] = analysis
    print("\nTopic Analysis:")
    print("=" * 80)
    print(analysis)
    print("=" * 80)

    # Step 2: Source analysis
    log.info("Finding and analyzing sources...")
    sources = await agent.find_sources(topic=topic, max_sources=max_sources)
    outputs["sources"] = sources
    print("\nRelevant Sources:")
    print("=" * 80)
    print(sources)
    print("=" * 80)

    # Step 3: Synthesize findings
    if sources:
        log.info("Synthesizing findings...")
        synthesis = await agent.analyze_sources(sources=sources)
        outputs["recommendations"] = synthesis
        print("\nSource Analysis and Synthesis:")
        print("=" * 80)
        print(synthesis)
        print("=" * 80)

    return outputs


async def main() -> None:
    """Run the research assistant example."""
    # Initialize configurations
    workflow_config = await setup_workflow()
    agent = await setup_agent()

    try:
        # Define the research topic
        topic = "Large Language Models and their impact on scientific research"

        # Run the research workflow
        outputs = await run_research_workflow(agent, workflow_config, topic)

        # Log workflow completion
        log.info(
            "Research workflow completed",
            outputs=list(outputs.keys()),
        )

    finally:
        # Cleanup agent
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
