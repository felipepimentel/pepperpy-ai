"""LangChain framework adapter.

This module provides adapter classes for integrating with the LangChain framework.
"""

from typing import Protocol, runtime_checkable
from uuid import uuid4

from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus

from .base import BaseFrameworkAdapter


@runtime_checkable
class AgentAction(Protocol):
    """Protocol for LangChain agent actions."""

    tool: str
    tool_input: str
    log: str


@runtime_checkable
class AgentFinish(Protocol):
    """Protocol for LangChain agent finish states."""

    return_values: dict[str, str]
    log: str


@runtime_checkable
class LangChainMessage(Protocol):
    """Protocol for LangChain messages."""

    content: str
    role: str


class SimpleLangChainMessage:
    """Simple implementation of LangChainMessage protocol."""

    def __init__(self, content: str, role: str) -> None:
        """Initialize a simple LangChain message.

        Args:
            content: Message content
            role: Message role/sender
        """
        self.content = content
        self.role = role


class SimpleAgentFinish:
    """Simple implementation of AgentFinish protocol."""

    def __init__(self, return_values: dict[str, str], log: str) -> None:
        """Initialize a simple agent finish state.

        Args:
            return_values: Dictionary of return values
            log: Log message
        """
        self.return_values = return_values
        self.log = log


class LangChainAdapter(BaseFrameworkAdapter[str, LangChainMessage, AgentFinish]):
    """Adapter for LangChain framework.

    This adapter allows Pepperpy agents to be used with LangChain.
    """

    async def to_framework_agent(self) -> str:
        """Convert Pepperpy agent to LangChain agent.

        Returns:
            The LangChain agent name

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return self.agent.name
        except AttributeError as e:
            raise ConversionError(f"Failed to convert to LangChain agent: {e}") from e

    async def from_framework_message(self, message: LangChainMessage) -> Message:
        """Convert LangChain message to Pepperpy message.

        Args:
            message: LangChain message to convert

        Returns:
            Pepperpy Message instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Message(
                id=uuid4(),
                type=MessageType.QUERY,
                sender=message.role,
                receiver="pepperpy",
                content={"text": message.content},
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(
                f"Failed to convert from LangChain message: {e}"
            ) from e

    async def to_framework_message(self, message: Message) -> LangChainMessage:
        """Convert Pepperpy message to LangChain message.

        Args:
            message: Pepperpy Message instance

        Returns:
            LangChain message

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return SimpleLangChainMessage(
                content=message.content.get("text", ""),
                role=message.sender,
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(f"Failed to convert to LangChain message: {e}") from e

    async def from_framework_response(self, response: AgentFinish) -> Response:
        """Convert a LangChain AgentFinish to a Pepperpy response.

        Args:
            response: LangChain AgentFinish instance

        Returns:
            Pepperpy Response instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            # Verify the response has the required attributes
            if not hasattr(response, "return_values") or not hasattr(response, "log"):
                raise ConversionError("Response does not match AgentFinish protocol")

            return Response(
                id=uuid4(),
                message_id=uuid4(),
                status=ResponseStatus.SUCCESS,
                content={"text": response.return_values.get("output", "")},
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(
                f"Failed to convert from LangChain response: {e}"
            ) from e

    async def to_framework_response(self, response: Response) -> AgentFinish:
        """Convert Pepperpy response to LangChain response.

        Args:
            response: Pepperpy Response instance

        Returns:
            LangChain AgentFinish instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return SimpleAgentFinish(
                return_values={"output": response.content.get("text", "")},
                log="Response generated by Pepperpy agent",
            )
        except (AttributeError, TypeError) as e:
            raise ConversionError(
                f"Failed to convert to LangChain response: {e}"
            ) from e
