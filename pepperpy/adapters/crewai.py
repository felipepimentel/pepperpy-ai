"""CrewAI framework adapter.

This module implements the adapter for the CrewAI framework.
"""

from typing import Any
from uuid import UUID, uuid4

from crewai import Agent as CrewAIAgent

from pepperpy.adapters.base import BaseFrameworkAdapter
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus


class CrewAIAdapter(BaseFrameworkAdapter[CrewAIAgent]):
    """Adapter for CrewAI framework.

    This adapter allows Pepperpy agents to be used as CrewAI agents
    and vice versa.

    Args:
        agent: The Pepperpy agent to adapt
        **kwargs: Additional CrewAI-specific configuration
    """

    async def to_framework_agent(self) -> CrewAIAgent:
        """Convert Pepperpy agent to CrewAI agent.

        Returns:
            CrewAI agent instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return CrewAIAgent(
                name=self.agent.name,
                goal=self.agent.description,
                backstory=self.agent.context.metadata.get("backstory", ""),
                allow_delegation=self.agent.context.metadata.get(
                    "allow_delegation", True
                ),
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert to CrewAI agent: {e}") from e

    async def from_framework_message(self, message: Any) -> Message:
        """Convert CrewAI message to Pepperpy message.

        Args:
            message: CrewAI message

        Returns:
            Pepperpy Message instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Message(
                type=MessageType.QUERY,
                sender=str(message.get("sender", "crewai")),
                receiver=str(message.get("receiver", "pepperpy")),
                content={"text": str(message.get("content", ""))},
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert from CrewAI message: {e}") from e

    async def to_framework_message(self, message: Message) -> dict[str, Any]:
        """Convert Pepperpy message to CrewAI message.

        Args:
            message: Pepperpy Message instance

        Returns:
            CrewAI message dict

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return {
                "content": message.content.get("text", ""),
                "sender": message.sender,
                "receiver": message.receiver,
            }
        except Exception as e:
            raise ConversionError(f"Failed to convert to CrewAI message: {e}") from e

    async def from_framework_response(self, response: Any) -> Response:
        """Convert CrewAI response to Pepperpy response.

        Args:
            response: CrewAI response

        Returns:
            Pepperpy Response instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Response(
                message_id=UUID(str(response.get("message_id", uuid4()))),
                status=ResponseStatus.SUCCESS,
                content={"text": str(response.get("content", ""))},
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert from CrewAI response: {e}") from e

    async def to_framework_response(self, response: Response) -> dict[str, Any]:
        """Convert Pepperpy response to CrewAI response.

        Args:
            response: Pepperpy Response instance

        Returns:
            CrewAI response dict

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return {
                "content": response.content.get("text", ""),
                "message_id": str(response.message_id),
                "status": response.status,
            }
        except Exception as e:
            raise ConversionError(f"Failed to convert to CrewAI response: {e}") from e
