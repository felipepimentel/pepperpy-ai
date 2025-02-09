"""Semantic Kernel framework adapter.

This module implements the adapter for the Microsoft Semantic Kernel framework.
"""

from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypeVar, runtime_checkable
from uuid import uuid4

from pepperpy.adapters.base import BaseFrameworkAdapter, ConfigValue
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.base import AgentProtocol
from pepperpy.core.types import (
    Message,
    MessageType,
    MetadataDict,
    Response,
    ResponseStatus,
)

# Type variables
T = TypeVar("T")  # Generic type variable for the SKFunction decorator


@runtime_checkable
class Variables(Protocol):
    """Protocol for Semantic Kernel variables."""

    input: str

    def to_dict(self) -> dict[str, Any]:
        """Convert variables to dictionary."""
        ...

    def update(self, data: dict[str, Any]) -> None:
        """Update variables with data."""
        ...


@runtime_checkable
class SKContextProtocol(Protocol):
    """Protocol for Semantic Kernel context."""

    variables: Variables
    result: str


@runtime_checkable
class KernelProtocol(Protocol):
    """Protocol for Semantic Kernel's Kernel class."""

    def register_semantic_function(
        self,
        skill_name: str,
        function_name: str,
        description: str,
        function: Callable[..., Any],
    ) -> None:
        """Register a semantic function with the kernel."""
        ...

    def create_new_context(self) -> SKContextProtocol:
        """Create a new context."""
        ...


# Define stub classes for type checking
class _StubVariables(Variables):
    """Stub for variables class."""

    def __init__(self) -> None:
        """Initialize variables."""
        self.input: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert variables to dictionary."""
        return {"input": self.input}

    def update(self, data: dict[str, Any]) -> None:
        """Update variables with data."""
        if "input" in data:
            self.input = str(data["input"])


class _StubContext(SKContextProtocol):
    """Stub for Semantic Kernel's SKContext class."""

    def __init__(self) -> None:
        """Initialize the context."""
        self.variables = _StubVariables()
        self.result = ""


class _StubKernel(KernelProtocol):
    """Stub for Semantic Kernel's Kernel class."""

    def register_semantic_function(
        self,
        skill_name: str,
        function_name: str,
        description: str,
        function: Callable[..., Any],
    ) -> None:
        """Register a semantic function with the kernel."""

    def create_new_context(self) -> SKContextProtocol:
        """Create a new context."""
        return _StubContext()


def _sk_function(
    description: str = "",
    name: str = "",
    input_description: str = "",
    output_description: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # type: ignore[misc]
    """Stub for SKFunction decorator."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


# Import real implementations if available
try:
    import semantic_kernel  # type: ignore
    import semantic_kernel.orchestration.sk_context  # type: ignore

    has_semantic_kernel = True
    KernelImpl = semantic_kernel.Kernel
    ContextImpl = semantic_kernel.orchestration.sk_context.SKContext
    sk_function = semantic_kernel.sk_function  # type: ignore
except ImportError:
    has_semantic_kernel = False
    KernelImpl = _StubKernel
    ContextImpl = _StubContext
    sk_function = _sk_function


class SemanticKernelAdapter(
    BaseFrameworkAdapter[KernelProtocol, SKContextProtocol, SKContextProtocol]
):
    """Adapter for Semantic Kernel framework.

    This adapter allows Pepperpy agents to be used as Semantic Kernel skills
    and vice versa.

    Args:
        agent (
            AgentProtocol[
                Message,
                Response,
                Mapping[str, ConfigValue],
                Message
            ]
        ): The Pepperpy agent to adapt
        **kwargs: Additional Semantic Kernel-specific configuration
    """

    def __init__(
        self,
        agent: AgentProtocol[Message, Response, Mapping[str, ConfigValue], Message],
        **kwargs: ConfigValue,
    ) -> None:
        """Initialize adapter with Pepperpy agent."""
        super().__init__(agent, **kwargs)
        self._kernel: KernelProtocol = KernelImpl()

    async def to_framework_agent(self) -> KernelProtocol:
        """Convert Pepperpy agent to Semantic Kernel kernel.

        Returns:
            KernelProtocol: Semantic Kernel Kernel instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            return self._kernel
        except Exception as e:
            raise ConversionError(f"Failed to convert to SK kernel: {e}") from e

    @sk_function(  # type: ignore[misc]
        description="Process a message using Pepperpy agent",
        name="process_message",
        input_description="The message to process",
        output_description="The processed result",
    )
    async def process_message(self, context: SKContextProtocol) -> str:
        """Process a message using Pepperpy agent.

        Args:
            context (SKContextProtocol): The context containing the message to process

        Returns:
            str: The processed result as a string

        Raises:
            ConversionError: If message processing fails
        """
        try:
            # Convert to Pepperpy message
            message = await self.from_framework_message(context)

            # Process with Pepperpy agent
            response = await self.agent.process(message)

            # Convert response back to string
            sk_response = await self.to_framework_response(response)
            return str(sk_response.variables.input)

        except Exception as e:
            raise ConversionError(f"Failed to process message: {e}") from e

    async def from_framework_message(self, message: SKContextProtocol) -> Message:
        """Convert Semantic Kernel context to Pepperpy message.

        Args:
            message (SKContextProtocol): The Semantic Kernel context to convert

        Returns:
            Message: The converted Pepperpy message

        Raises:
            ConversionError: If conversion fails
        """
        try:
            variables = message.variables.to_dict()
            metadata: MetadataDict = {"context": str(variables)}
            return Message(
                id=uuid4(),
                type=MessageType.COMMAND,
                sender="semantic_kernel",
                receiver="pepperpy",
                content={"input": message.variables.input},
                metadata=metadata,
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert SK message: {e}") from e

    async def to_framework_message(self, message: Message) -> SKContextProtocol:
        """Convert Pepperpy message to Semantic Kernel context.

        Args:
            message (Message): The Pepperpy message to convert

        Returns:
            SKContextProtocol: The converted Semantic Kernel context

        Raises:
            ConversionError: If conversion fails
        """
        try:
            context = ContextImpl()
            context.variables.update(message.content)
            return context
        except Exception as e:
            raise ConversionError(f"Failed to convert to SK message: {e}") from e

    async def from_framework_response(self, response: SKContextProtocol) -> Response:
        """Convert Semantic Kernel response to Pepperpy response.

        Args:
            response (SKContextProtocol): The Semantic Kernel function context
                to convert

        Returns:
            Response: The converted Pepperpy response

        Raises:
            ConversionError: If conversion fails
        """
        try:
            variables = response.variables.to_dict()
            metadata: MetadataDict = {"context": str(variables)}
            return Response(
                id=uuid4(),
                message_id=uuid4(),  # Since we don't have the original message ID
                status=ResponseStatus.SUCCESS,
                content={"output": response.result},
                metadata=metadata,
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert SK response: {e}") from e

    async def to_framework_response(self, response: Response) -> SKContextProtocol:
        """Convert Pepperpy response to Semantic Kernel context.

        Args:
            response (Response): The Pepperpy response to convert

        Returns:
            SKContextProtocol: The converted Semantic Kernel context

        Raises:
            ConversionError: If conversion fails
        """
        try:
            context = ContextImpl()
            context.variables.update(response.content)
            return context
        except Exception as e:
            raise ConversionError(f"Failed to convert to SK response: {e}") from e
