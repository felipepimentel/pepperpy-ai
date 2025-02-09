"""CrewAI framework adapter.

This module provides adapter classes for integrating with the CrewAI framework.
"""

from typing import Protocol
from uuid import uuid4

from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus

from .base import BaseFrameworkAdapter


class CrewAIMessage(Protocol):
    """Protocol for CrewAI messages."""

    content: str
    role: str


class CrewAIResponse(Protocol):
    """Protocol for CrewAI responses."""

    content: str
    role: str


class CrewAIAdapter(BaseFrameworkAdapter[str, CrewAIMessage, CrewAIResponse]):
    """Adapter for CrewAI framework.

    This adapter allows Pepperpy agents to be used with CrewAI.
    """

    async def to_framework_agent(self) -> str:
        """Convert Pepperpy agent to CrewAI agent.

        Returns:
            The CrewAI agent name

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return self.agent.name
        except AttributeError as e:
            raise ConversionError(f"Failed to convert to CrewAI agent: {e}") from e

    async def from_framework_message(self, message: CrewAIMessage) -> Message:
        """Convert CrewAI message to Pepperpy message.

        Args:
            message: CrewAI message to convert

        Returns:
            Pepperpy Message instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Message(
                type=MessageType.QUERY,
                sender=message.role,
                receiver="pepperpy",
                content={"text": message.content},
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(f"Failed to convert from CrewAI message: {e}") from e

    async def to_framework_message(self, message: Message) -> CrewAIMessage:
        """Convert Pepperpy message to CrewAI message.

        Args:
            message: Pepperpy Message instance

        Returns:
            CrewAI message

        Raises:
            ConversionError: If conversion fails
        """
        try:
            # Create a simple object that matches the CrewAIMessage protocol
            class SimpleCrewAIMessage:
                def __init__(self, content: str, role: str) -> None:
                    self.content = content
                    self.role = role

            return SimpleCrewAIMessage(
                content=message.content.get("text", ""),
                role=message.sender,
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(f"Failed to convert to CrewAI message: {e}") from e

    async def from_framework_response(self, response: CrewAIResponse) -> Response:
        """Convert CrewAI response to Pepperpy response.

        Args:
            response: CrewAI response to convert

        Returns:
            Pepperpy Response instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Response(
                message_id=uuid4(),
                status=ResponseStatus.SUCCESS,
                content={"text": response.content},
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(f"Failed to convert from CrewAI response: {e}") from e

    async def to_framework_response(self, response: Response) -> CrewAIResponse:
        """Convert Pepperpy response to CrewAI response.

        Args:
            response: Pepperpy Response instance

        Returns:
            CrewAI response

        Raises:
            ConversionError: If conversion fails
        """
        try:
            # Create a simple object that matches the CrewAIResponse protocol
            class SimpleCrewAIResponse:
                def __init__(self, content: str, role: str) -> None:
                    self.content = content
                    self.role = role

            return SimpleCrewAIResponse(
                content=response.content.get("text", ""),
                role="assistant",
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(f"Failed to convert to CrewAI response: {e}") from e
