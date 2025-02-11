"""Research agent implementation for the Pepperpy framework.

This module provides the research agent that can perform research tasks
using LLM capabilities.
"""

from typing import Any, Dict, List, Optional

from pepperpy.core.base import BaseAgent
from pepperpy.core.errors import ConfigurationError
from pepperpy.core.types import (
    AgentCapability,
    Message,
    MessageContent,
    MessageType,
    ResearchDepth,
    ResearchFocus,
    ResearchResults,
    Response,
)
from pepperpy.monitoring import logger as log


class ResearchAgent(BaseAgent):
    """Research agent implementation.

    This agent can perform research tasks using LLM capabilities.
    It supports different research depths and focus areas.

    Attributes
    ----------
        client: The Pepperpy client instance
        config: Agent configuration
        _depth: Research depth setting
        _focus: Research focus areas
        _max_sources: Maximum number of sources to use

    """

    def __init__(self, client: Any, config: Dict[str, Any]) -> None:
        """Initialize the research agent.

        Args:
        ----
            client: The Pepperpy client instance
            config: Agent configuration

        """
        super().__init__(client, config)
        self._depth: Optional[ResearchDepth] = None
        self._focus: Optional[List[ResearchFocus]] = None
        self._max_sources: Optional[int] = None

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the agent with configuration.

        Args:
        ----
            config: Agent configuration

        Raises:
        ------
            ConfigurationError: If configuration is invalid

        """
        await super().initialize(config)

        # Validate and set research depth
        depth = config.get("depth", "basic")
        if not isinstance(depth, str) or depth not in [
            "basic",
            "comprehensive",
            "deep",
        ]:
            raise ConfigurationError(f"Invalid research depth: {depth}")
        self._depth = depth

        # Validate and set research focus
        focus = config.get("focus", ["general"])
        if not isinstance(focus, list):
            focus = [focus]
        valid_focus = ["general", "academic", "industry", "technical", "business"]
        if not all(f in valid_focus for f in focus):
            raise ConfigurationError(f"Invalid research focus: {focus}")
        self._focus = focus

        # Validate and set max sources
        max_sources = config.get("max_sources", 5)
        if not isinstance(max_sources, int) or max_sources < 1:
            raise ConfigurationError(f"Invalid max sources: {max_sources}")
        self._max_sources = max_sources

        log.info(
            "Research agent initialized",
            depth=self._depth,
            focus=self._focus,
            max_sources=self._max_sources,
        )

    @property
    def capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities.

        Returns
        -------
            List of agent capabilities

        """
        return [
            AgentCapability.RESEARCH,
            AgentCapability.SUMMARIZE,
            AgentCapability.ANALYZE,
        ]

    async def process_message(self, message: Message) -> Response:
        """Process an incoming message.

        Args:
        ----
            message: Input message to process

        Returns:
        -------
            Agent response

        """
        if message.type != MessageType.USER:
            raise ConfigurationError(f"Unsupported message type: {message.type}")

        # Extract research topic from message
        topic = message.content.get("topic")
        if not topic:
            raise ConfigurationError("Research topic not provided")

        try:
            # Perform research
            results = await self._perform_research(topic)

            # Create response
            return Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.ASSISTANT,
                    content={
                        "results": results.dict(),
                        "metadata": {
                            "depth": self._depth,
                            "focus": self._focus,
                            "max_sources": self._max_sources,
                        },
                    },
                ),
                status="success",
            )

        except Exception as e:
            log.error(
                "Research failed",
                error=str(e),
                topic=topic,
                depth=self._depth,
                focus=self._focus,
            )
            raise

    async def _perform_research(self, topic: str) -> ResearchResults:
        """Perform research on a topic.

        Args:
        ----
            topic: Research topic

        Returns:
        -------
            Research results

        """
        # TODO: Implement actual research logic using LLM
        # For now return mock results
        return ResearchResults(
            topic=topic,
            summary="Mock research results",
            sources=["source1", "source2"],
            confidence=0.8,
            metadata={
                "depth": self._depth,
                "focus": self._focus,
                "max_sources": self._max_sources,
            },
        )
