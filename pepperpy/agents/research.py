"""Research agent implementation for the Pepperpy framework.

This module provides the research agent that can perform research tasks
using LLM capabilities.
"""

from typing import Any, List, Optional, cast

from loguru import logger

from pepperpy.core.base import AgentConfig, BaseAgent
from pepperpy.core.errors import ConfigurationError
from pepperpy.core.types import (
    Message,
    MessageContent,
    MessageType,
    ResearchDepth,
    ResearchFocus,
    ResearchResults,
    Response,
    ResponseStatus,
)


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

    def __init__(self, client: Any, config: AgentConfig) -> None:
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
        self._logger = logger.bind(agent=self.__class__.__name__)

    async def initialize(self) -> None:
        """Initialize the agent.

        Raises
        ------
            ConfigurationError: If configuration is invalid

        """
        await super().initialize()

        # Validate and set research depth
        depth = self._config.settings.get("depth", "basic")
        if not isinstance(depth, str) or depth not in [
            "basic",
            "comprehensive",
            "deep",
        ]:
            raise ConfigurationError(f"Invalid research depth: {depth}")
        self._depth = cast(ResearchDepth, depth)

        # Validate and set research focus
        focus = self._config.settings.get("focus", ["general"])
        if not isinstance(focus, list):
            focus = [focus]
        valid_focus = ["general", "academic", "industry", "technical", "business"]
        if not all(f in valid_focus for f in focus):
            raise ConfigurationError(f"Invalid research focus: {focus}")
        self._focus = [cast(ResearchFocus, f) for f in focus]

        # Validate and set max sources
        max_sources = self._config.settings.get("max_sources", 5)
        if not isinstance(max_sources, int) or max_sources < 1:
            raise ConfigurationError(f"Invalid max sources: {max_sources}")
        self._max_sources = max_sources

        self._logger.info(
            "Research agent initialized",
            depth=self._depth,
            focus=self._focus,
            max_sources=self._max_sources,
        )

    @property
    def capabilities(self) -> List[str]:
        """Get agent capabilities.

        Returns
        -------
            List of agent capabilities

        """
        return [
            "research",
            "summarize",
            "analyze",
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
        # Validate message type
        if message.type != MessageType.QUERY:
            raise ConfigurationError(f"Unsupported message type: {message.type}")

        # Extract research topic from message
        if isinstance(message.content, dict):
            topic = message.content.get("topic")
            if not topic:
                raise ConfigurationError("Research topic not provided")
        else:
            raise ConfigurationError("Invalid message content format")

        try:
            # Perform research
            results = await self._perform_research(topic)

            # Create response
            return Response(
                message_id=str(message.id),
                content=MessageContent(
                    type=MessageType.RESPONSE,
                    content={
                        "results": results.dict(),
                        "metadata": {
                            "depth": self._depth,
                            "focus": self._focus,
                            "max_sources": self._max_sources,
                        },
                    },
                ),
                status=ResponseStatus.SUCCESS,
            )

        except Exception as e:
            self._logger.error(
                "Research failed",
                error=str(e),
                topic=topic,
                depth=self._depth,
                focus=self._focus,
            )
            return Response(
                message_id=str(message.id),
                content=MessageContent(
                    type=MessageType.ERROR,
                    content={"error": str(e)},
                ),
                status=ResponseStatus.ERROR,
            )

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
