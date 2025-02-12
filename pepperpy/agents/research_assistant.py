"""Research Assistant Agent.

This module provides a research assistant agent that helps with academic research.
"""

from typing import Any, List
from uuid import uuid4

from pepperpy.core.base import AgentConfig, BaseAgent
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.types import (
    AgentState,
    Message,
    MessageContent,
    MessageType,
    Response,
    ResponseStatus,
)
from pepperpy.monitoring import logger


class ResearchAssistant(BaseAgent):
    """Research assistant agent that helps with academic research."""

    def __init__(self, client: Any, config: AgentConfig) -> None:
        """Initialize the research assistant.

        Args:
            client: The Pepperpy client instance
            config: Agent configuration

        Raises:
            ConfigurationError: If configuration is invalid

        """
        super().__init__(client, config)
        self._logger = logger.bind(agent=self.__class__.__name__)
        self._prompts = config.settings.get("prompts", {})

    @property
    def capabilities(self) -> List[str]:
        """Get agent capabilities."""
        return [
            "research",
            "analyze",
            "summarize",
        ]

    async def initialize(self) -> None:
        """Initialize the agent."""
        await super().initialize()
        self._logger.info("Research assistant initialized")

    async def analyze_topic(self, topic: str) -> Response:
        """Analyze a research topic.

        Args:
            topic: The topic to analyze

        Returns:
            Response containing the analysis

        """
        message_id = str(uuid4())
        message_content = MessageContent(
            type=MessageType.USER,
            content={"text": f"Please analyze the following topic: {topic}"},
        )

        # Send message to provider and get response
        response_text = await self._client.send_message(
            message_content["content"]["text"]
        )

        # Create response
        return Response(
            message_id=message_id,
            content=MessageContent(
                type=MessageType.ASSISTANT,
                content={"text": response_text},
            ),
            status=ResponseStatus.SUCCESS,
        )

    async def find_sources(self, query: str) -> Response:
        """Find relevant sources for a query.

        Args:
            query: The search query

        Returns:
            Response containing the sources

        """
        message_id = str(uuid4())
        message_content = MessageContent(
            type=MessageType.USER,
            content={"text": f"Please find relevant sources for: {query}"},
        )

        # Send message to provider and get response
        response_text = await self._client.send_message(
            message_content["content"]["text"]
        )

        # Create response
        return Response(
            message_id=message_id,
            content=MessageContent(
                type=MessageType.ASSISTANT,
                content={"text": response_text},
            ),
            status=ResponseStatus.SUCCESS,
        )

    async def synthesize(self, sources: List[str]) -> Response:
        """Synthesize information from sources.

        Args:
            sources: List of sources to synthesize

        Returns:
            Response containing the synthesis

        """
        message_id = str(uuid4())
        message_content = MessageContent(
            type=MessageType.USER,
            content={
                "text": f"Please synthesize information from these sources:\n{chr(10).join(sources)}"
            },
        )

        # Send message to provider and get response
        response_text = await self._client.send_message(
            message_content["content"]["text"]
        )

        # Create response
        return Response(
            message_id=message_id,
            content=MessageContent(
                type=MessageType.ASSISTANT,
                content={"text": response_text},
            ),
            status=ResponseStatus.SUCCESS,
        )

    async def process_message(self, message: Message) -> Response:
        """Process an incoming message.

        Args:
            message: The message to process

        Returns:
            The response to the message

        Raises:
            StateError: If agent is not initialized

        """
        if not self._initialized:
            raise StateError("Agent is not initialized")

        try:
            self._state = AgentState.PROCESSING
            logger.debug("Processing message: %s", message)

            # Validate message type
            if message.type != MessageType.USER:
                raise ConfigurationError(f"Unsupported message type: {message.type}")

            # Get the text content from the message
            if isinstance(message.content, dict) and "text" in message.content:
                text = str(message.content["text"])
            else:
                text = str(message.content)

            # Send message to provider and get response
            response_text = await self._client.send_message(text)

            # Create response
            response = Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.ASSISTANT,
                    content={"text": response_text},
                ),
                status=ResponseStatus.SUCCESS,
            )

            self._state = AgentState.READY
            return response

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to process message: %s", e)
            return Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.ASSISTANT,
                    content={"error": str(e)},
                ),
                status=ResponseStatus.ERROR,
            )
