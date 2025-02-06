"""Semantic Kernel framework adapter.

This module implements the adapter for the Microsoft Semantic Kernel framework.
"""

from typing import Any, TypeVar
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.orchestration.sk_function_context import SKFunctionContext

from pepperpy.adapters.base import BaseFrameworkAdapter
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.base import AgentProtocol
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus

T = TypeVar("T")


class SemanticKernelAdapter(BaseFrameworkAdapter[Kernel]):
    """Adapter for Semantic Kernel framework.

    This adapter allows Pepperpy agents to be used as Semantic Kernel skills
    and vice versa.

    Args:
        agent (AgentProtocol[Any, Any, Any, Any]): The Pepperpy agent to adapt
        **kwargs: Additional Semantic Kernel-specific configuration

    Attributes:
        _kernel (Kernel): The Semantic Kernel instance
        _adapter (SemanticKernelAdapter): Reference to self for convenience
    """

    def __init__(self, agent: AgentProtocol[Any, Any, Any, Any]) -> None:
        """Initialize adapter with Pepperpy agent."""
        super().__init__(agent)
        self._kernel = Kernel()
        self._adapter = self

    async def to_framework_agent(self) -> Kernel:
        """Convert Pepperpy agent to Semantic Kernel kernel.

        Returns:
            Kernel: Semantic Kernel Kernel instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return self._kernel
        except Exception as e:
            raise ConversionError(f"Failed to convert to SK kernel: {e}") from e

    @SKFunction(  # type: ignore[misc]
        description="Process a message using Pepperpy agent",
        name="process_message",
        input_description="The message to process",
        output_description="The processed result",
    )
    async def process_message(self, context: SKContext) -> str:
        """Process a message using Pepperpy agent.

        Args:
            context (SKContext): The Semantic Kernel context containing the message

        Returns:
            str: The processed result as a string

        Raises:
            ConversionError: If message processing fails
        """
        try:
            # Convert to Pepperpy message
            message = await self._adapter.from_framework_message(context)

            # Process with Pepperpy agent
            response = await self._adapter.agent.process(message)

            # Convert response back to string
            sk_response = await self._adapter.to_framework_response(response)
            return str(sk_response.variables.input)

        except Exception as e:
            raise ConversionError(f"Failed to process message: {e}") from e

    async def from_framework_message(self, context: SKContext) -> Message:
        """Convert Semantic Kernel context to Pepperpy message.

        Args:
            context (SKContext): The Semantic Kernel context to convert

        Returns:
            Message: The converted Pepperpy message

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Message(
                id=uuid4(),
                type=MessageType.COMMAND,
                sender="semantic_kernel",
                receiver="pepperpy",
                content={"input": context.variables.input},
                metadata={"context": context.variables.to_dict()},
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert SK message: {e}") from e

    async def to_framework_message(self, message: Message) -> SKContext:
        """Convert Pepperpy message to Semantic Kernel context.

        Args:
            message (Message): The Pepperpy message to convert

        Returns:
            SKContext: The converted Semantic Kernel context

        Raises:
            ConversionError: If conversion fails
        """
        try:
            context = SKContext()
            context.variables.update(message.content)
            return context
        except Exception as e:
            raise ConversionError(f"Failed to convert to SK message: {e}") from e

    async def from_framework_response(self, response: SKFunctionContext) -> Response:
        """Convert Semantic Kernel response to Pepperpy response.

        Args:
            response (SKFunctionContext): The Semantic Kernel function context
                to convert

        Returns:
            Response: The converted Pepperpy response

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return Response(
                id=uuid4(),
                message_id=uuid4(),  # Since we don't have the original message ID
                status=ResponseStatus.SUCCESS,
                content={"output": response.result},
                metadata={"context": response.variables.to_dict()},
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert SK response: {e}") from e

    async def to_framework_response(self, response: Response) -> SKContext:
        """Convert Pepperpy response to Semantic Kernel context.

        Args:
            response (Response): The Pepperpy response to convert

        Returns:
            SKContext: The converted Semantic Kernel context

        Raises:
            ConversionError: If conversion fails
        """
        try:
            context = SKContext()
            context.variables.update(response.content)
            return context
        except Exception as e:
            raise ConversionError(f"Failed to convert to SK response: {e}") from e
