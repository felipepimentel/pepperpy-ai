"""Example demonstrating the research assistant agent capabilities using the simplified Pepperpy structure.

This example shows how to use the research assistant agent with the new unified configuration
and initialization system to analyze research topics, find relevant sources, and synthesize information.

Example:
-------
    ```python
    # Simple usage with automatic configuration
    async with PepperpyClient.auto() as client:
        results = await client.run(
            "research_assistant",
            "analyze",
            topic="AI in Healthcare",
            max_sources=5
        )
        print(results["summary"])

    # Advanced usage with custom configuration
    async with PepperpyClient(cache_enabled=True) as client:
        results = await client.run_workflow(
            "research/comprehensive",
            topic="AI in Healthcare",
            requirements={
                "depth": "expert",
                "focus": ["academic", "industry"]
            }
        )
        print(results["key_findings"])
    ```

"""

import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,
    TypeVar,
    Union,
)

from dotenv import load_dotenv

from pepperpy import PepperpyClient
from pepperpy.core.base import AgentState, BaseAgent
from pepperpy.core.config import PepperpyConfig
from pepperpy.core.factory import Factory
from pepperpy.core.types import ResearchDepth, ResearchFocus, ResearchResults
from pepperpy.monitoring import logger
from pepperpy.providers.base import ProviderCallback

# Type variables for agent creation
T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")
T_Config = TypeVar("T_Config", bound=Dict[str, Any])
T_Context = TypeVar("T_Context")

log = logger.bind(example="research_assistant")

# Default hub directory in user's home
HUB_DIR = Path.home() / ".pepper_hub"

# Type definitions for better code clarity
ResearchDepth = Literal["basic", "comprehensive", "expert"]
ResearchFocus = Literal["academic", "industry", "general"]


class ResearchRequirements(TypedDict):
    """Type definition for research requirements configuration."""

    depth: ResearchDepth
    focus: Union[ResearchFocus, List[ResearchFocus]]
    max_sources: int
    min_confidence: float
    include_metadata: bool
    source_types: List[str]
    language: str


class ResearchResults(TypedDict):
    """Type definition for research results."""

    summary: str
    sources: List[Dict[str, Any]]
    key_findings: List[str]
    recommendations: Optional[List[str]]
    methodology: Optional[str]
    limitations: Optional[str]
    future_work: Optional[str]


@dataclass
class ResearchProgress:
    """Tracks the progress of research tasks."""

    total_steps: int
    current_step: int
    status: str
    details: Optional[str] = None


# Type alias for progress callback
ProgressCallback = ProviderCallback


def create_agent_factory(client: PepperpyClient) -> Factory:
    """Create an agent factory for the research assistant.

    Args:
    ----
        client: The Pepperpy client instance

    Returns:
    -------
        Agent factory instance

    """
    from pepperpy.agents.factory import AgentFactory

    return AgentFactory(client)


def load_env_config() -> Dict[str, Any]:
    """Load environment configuration.

    Returns
    -------
        Dictionary with environment configuration

    """
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    return {
        "provider_type": "openrouter",  # Use openrouter as the provider
        "provider_config": {
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4-turbo-preview"),
        },
    }


class SimpleResearchAssistant(BaseAgent):
    """Simple implementation of a research assistant agent."""

    def __init__(self, client: PepperpyClient, config: Dict[str, Any]) -> None:
        """Initialize the research assistant.

        Args:
        ----
            client: The Pepperpy client instance
            config: Agent configuration

        """
        super().__init__(
            name=config["name"],
            description=config["description"],
            version=config["version"],
        )
        self.client = client
        self.config = config

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent with the given configuration."""
        await self._update_state(AgentState.INITIALIZING)
        try:
            await self._initialize_impl(config)
            await self._update_state(AgentState.READY)
        except Exception as e:
            await self._update_state(AgentState.ERROR)
            raise e

    async def process(self, input_data: Any, context: Optional[Any] = None) -> Any:
        """Process the input data using the agent."""
        if self._state != AgentState.READY:
            raise RuntimeError(
                f"Agent must be in READY state to process, current state: {self._state}"
            )

        await self._update_state(AgentState.PROCESSING)
        try:
            result = await self._process_impl(input_data, context)
            await self._update_state(AgentState.READY)
            return result
        except Exception as e:
            await self._update_state(AgentState.ERROR)
            raise e

    async def cleanup(self) -> None:
        """Clean up any resources used by the agent."""
        if self._state == AgentState.TERMINATED:
            return

        await self._update_state(AgentState.CLEANING)
        try:
            await self._cleanup_impl()
            await self._update_state(AgentState.TERMINATED)
        except Exception as e:
            await self._update_state(AgentState.ERROR)
            raise e

    async def _initialize_impl(self, config: Dict[str, Any]) -> None:
        """Internal initialization implementation."""
        # No special initialization needed for this simple example
        pass

    async def _process_impl(
        self, input_data: Any, context: Optional[Any] = None
    ) -> Any:
        """Internal process implementation."""
        return await self.client.send_message(str(input_data))

    async def _cleanup_impl(self) -> None:
        """Internal cleanup implementation."""
        # No special cleanup needed for this simple example
        pass


async def run_simple_research(
    topic: str,
    max_sources: int = 5,
    depth: ResearchDepth = "comprehensive",
    focus: Union[ResearchFocus, List[ResearchFocus]] = "general",
    cache: bool = True,
) -> ResearchResults:
    """Run a simple research workflow using automatic configuration.

    This demonstrates the most straightforward way to use the research assistant
    with zero configuration required.

    Args:
    ----
        topic: The research topic to investigate.
        max_sources: Maximum number of sources to include (default: 5).
        depth: Desired research depth (default: "comprehensive").
        focus: Research focus areas (default: "general").
        cache: Whether to use caching (default: True).

    Returns:
    -------
        A ResearchResults dictionary containing the research findings.

    Raises:
    ------
        ValueError: If invalid research parameters are provided.
        ResearchError: If the research process encounters an error.

    """
    # Prepare requirements first
    requirements = {
        "depth": depth,
        "focus": [focus] if isinstance(focus, str) else focus,
        "max_sources": max_sources,
    }

    try:
        # Create client with environment configuration
        env_config = load_env_config()
        config = PepperpyConfig(**env_config)

        # Use the new auto-configuration feature
        async with PepperpyClient.auto() as client:
            # Run the research workflow directly
            result = await client.run(
                "research_assistant",
                "analyze",
                topic=topic,
                requirements=requirements,
                cache=cache,
            )
            return result

    except Exception as e:
        log.error(
            "Failed to run simple research",
            error=str(e),
            topic=topic,
            requirements=requirements,
        )
        raise


async def run_advanced_research(
    topic: str,
    requirements: ResearchRequirements,
    workflow_name: str = "research/comprehensive",
    cache: bool = True,
    custom_config: Optional[Dict[str, Any]] = None,
) -> ResearchResults:
    """Run an advanced research workflow with custom configuration.

    This demonstrates using workflows and multiple coordinated agents for more
    complex research tasks with customizable requirements.

    Args:
    ----
        topic: The research topic to investigate.
        requirements: Detailed research requirements configuration.
        workflow_name: Name of the workflow to use (default: "research/comprehensive").
        cache: Whether to use caching (default: True).
        custom_config: Optional custom configuration for the client.

    Returns:
    -------
        A ResearchResults dictionary containing the research findings.

    Raises:
    ------
        WorkflowNotFoundError: If the specified workflow doesn't exist.
        ResearchError: If the research process encounters an error.

    """
    try:
        # Load environment config and merge with custom config
        env_config = load_env_config()
        if custom_config:
            env_config.update(custom_config)

        # Create client with configuration
        config = PepperpyConfig(**env_config)

        # Use the new workflow execution feature
        async with PepperpyClient(config=config, cache_enabled=cache) as client:
            # Run the workflow with requirements
            result = await client.run_workflow(
                workflow_name,
                topic=topic,
                requirements=requirements,
            )
            return result

    except Exception as e:
        log.error(
            "Failed to run advanced research",
            error=str(e),
            topic=topic,
            workflow=workflow_name,
            requirements=requirements,
        )
        raise


async def main() -> None:
    """Run the research assistant example."""
    try:
        # Ensure environment is properly configured
        load_env_config()

        # Simple research example
        print("\nRunning simple research example...")
        result = await run_simple_research(
            topic="Large Language Models and their impact on scientific research",
            max_sources=5,
            depth="comprehensive",
            focus=["academic", "industry"],
        )
        print("\nSimple Research Results:")
        print(json.dumps(result.dict(), indent=2))

        # Advanced research example
        print("\nRunning advanced research example...")
        requirements = ResearchRequirements(
            depth="expert",
            focus=["academic", "industry"],
            max_sources=10,
            min_confidence=0.8,
            include_metadata=True,
            source_types=["academic", "industry", "news"],
            language="en",
        )

        result = await run_advanced_research(
            topic="The future of AI safety and regulation",
            requirements=requirements,
            workflow_name="research/comprehensive",
            cache=True,
        )
        print("\nAdvanced Research Results:")
        print(json.dumps(result.dict(), indent=2))

    except Exception as e:
        log.error("Research assistant failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
