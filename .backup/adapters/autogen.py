"""AutoGen framework adapter.

This module implements the adapter for the AutoGen framework.
"""

from importlib.util import find_spec
from typing import Any, Dict, NotRequired, Protocol, TypedDict, TypeVar, cast
from uuid import uuid4

from pepperpy.adapters.base import BaseFrameworkAdapter
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import (
    Message,
    MessageContent,
    MessageType,
    Response,
    ResponseStatus,
)

# Define type variables for type checking
T_AutoGenAgent = TypeVar("T_AutoGenAgent", bound="AutoGenAgent")
T_ConversableAgent = TypeVar("T_ConversableAgent", bound="ConversableAgent")


class AutoGenMessage(TypedDict):
    """Type for AutoGen messages."""

    sender: str
    receiver: str
    content: str


class AutoGenConfig(TypedDict):
    """Type for AutoGen configuration."""

    name: str
    max_consecutive_auto_reply: NotRequired[int]
    human_input_mode: NotRequired[str]
    llm_config: NotRequired[dict[str, Any]]
    code_execution_config: NotRequired[dict[str, Any]]


# Base Protocol classes for type checking
class AutoGenAgent(Protocol):
    """Protocol for AutoGen Agent."""

    name: str

    async def send(self, message: AutoGenMessage, recipient: "AutoGenAgent") -> None:
        """Send message."""
        ...

    async def receive(self, message: AutoGenMessage, sender: "AutoGenAgent") -> None:
        """Receive message."""
        ...


class ConversableAgent(Protocol):
    """Protocol for AutoGen ConversableAgent."""

    name: str

    def __init__(self, name: str, **kwargs: dict[str, Any]) -> None:
        """Initialize agent."""
        ...

    async def send(self, message: AutoGenMessage, recipient: AutoGenAgent) -> None:
        """Send message."""
        ...

    async def receive(self, message: AutoGenMessage, sender: AutoGenAgent) -> None:
        """Receive message."""
        ...


# Check if autogen is available
has_autogen = bool(find_spec("autogen"))

# Runtime imports - ignore type errors since autogen is optional
if has_autogen:
    try:
        import autogen  # type: ignore

        RuntimeAutoGenAgent = autogen.Agent  # type: ignore
        RuntimeConversableAgent = autogen.ConversableAgent  # type: ignore
    except ImportError:
        RuntimeAutoGenAgent = None  # type: ignore
        RuntimeConversableAgent = None  # type: ignore


class AutoGenAdapter(
    BaseFrameworkAdapter[T_AutoGenAgent, AutoGenMessage, AutoGenMessage]
):
    """Adapter for AutoGen framework.

    This adapter allows Pepperpy agents to be used as AutoGen agents
    and vice versa.

    Args:
        agent: The Pepperpy agent to adapt
        **kwargs: Additional AutoGen-specific configuration

    """

    async def to_framework_agent(self) -> T_AutoGenAgent:
        """Convert Pepperpy agent to AutoGen agent.

        Returns:
            AutoGen agent instance

        Raises:
            ConversionError: If conversion fails

        """
        if not has_autogen:
            raise ConversionError(
                "AutoGen is not installed. Please install it with: pip install autogen"
            )

        try:
            # Create a custom AutoGen agent class that wraps Pepperpy agent
            class PepperpyAutoGenAgent(ConversableAgent):  # type: ignore
                name: str

                def __init__(
                    self,
                    adapter: "AutoGenAdapter[T_AutoGenAgent]",
                    name: str,
                    **kwargs: dict[str, Any],
                ) -> None:
                    self.name = name
                    self._adapter = adapter

                async def send(
                    self, message: AutoGenMessage, recipient: AutoGenAgent
                ) -> None:
                    """Send message."""
                    pass

                async def receive(
                    self, message: AutoGenMessage, sender: AutoGenAgent
                ) -> None:
                    """Process received message using Pepperpy agent.

                    Args:
                        message: Message from AutoGen
                        sender: Message sender

                    """
                    try:
                        # Convert AutoGen message to Pepperpy format
                        pepperpy_message = await self._adapter.from_framework_message(
                            message
                        )

                        # Process with Pepperpy agent
                        response = await self._adapter.agent.process(pepperpy_message)

                        # Convert response back to AutoGen format
                        autogen_response = await self._adapter.to_framework_response(
                            response
                        )

                        # Send response
                        await self.send(autogen_response, sender)

                    except Exception as e:
                        raise ConversionError(f"Failed to process message: {e}") from e

            # Create and return the agent instance
            agent = PepperpyAutoGenAgent(self, name=str(self.agent.name))
            return cast(T_AutoGenAgent, agent)

        except Exception as e:
            raise ConversionError(f"Failed to convert to AutoGen agent: {e}") from e

    async def from_framework_message(self, message: AutoGenMessage) -> Message:
        """Convert AutoGen message to Pepperpy message.

        Args:
            message: AutoGen message

        Returns:
            Pepperpy Message instance

        Raises:
            ConversionError: If conversion fails

        """
        try:
            return Message(
                type=MessageType.QUERY,
                content={"text": str(message["content"])},
                id=uuid4(),
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert from AutoGen message: {e}") from e

    async def to_framework_message(self, message: Message) -> AutoGenMessage:
        """Convert Pepperpy message to AutoGen message.

        Args:
            message: Pepperpy message

        Returns:
            AutoGen message

        Raises:
            ConversionError: If conversion fails

        """
        try:
            content = cast(Dict[str, Any], message.content)
            text = content.get("text", "")
            return AutoGenMessage(
                sender=str(self.agent.name),
                receiver="user",  # Default to user as receiver
                content=str(text),
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert to AutoGen message: {e}") from e

    async def from_framework_response(self, response: AutoGenMessage) -> Response:
        """Convert AutoGen response to Pepperpy response.

        Args:
            response: AutoGen response

        Returns:
            Pepperpy Response instance

        Raises:
            ConversionError: If conversion fails

        """
        try:
            message_id = str(uuid4())
            content: MessageContent = {
                "type": MessageType.RESPONSE,
                "content": {"text": str(response["content"])},
            }
            return Response(
                message_id=message_id,
                status=ResponseStatus.SUCCESS,
                content=content,
                id=uuid4(),
            )
        except Exception as e:
            raise ConversionError(
                f"Failed to convert from AutoGen response: {e}"
            ) from e

    async def to_framework_response(self, response: Response) -> AutoGenMessage:
        """Convert Pepperpy response to AutoGen response.

        Args:
            response: Pepperpy Response instance

        Returns:
            AutoGen response dict

        Raises:
            ConversionError: If conversion fails

        """
        try:
            content = cast(Dict[str, Any], response.content.get("content", {}))
            text = content.get("text", "")
            return AutoGenMessage(
                sender=str(self.agent.name),
                receiver="user",  # Default to user as receiver
                content=str(text),
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert to AutoGen response: {e}") from e
