"""AutoGen framework adapter.

This module implements the adapter for the AutoGen framework.
"""

from typing import Any
from uuid import UUID, uuid4

from autogen import Agent as AutoGenAgent
from autogen import ConversableAgent

from pepperpy.adapters.base import BaseFrameworkAdapter
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus


class AutoGenAdapter(BaseFrameworkAdapter[AutoGenAgent]):
    """Adapter for AutoGen framework.

    This adapter allows Pepperpy agents to be used as AutoGen agents
    and vice versa.

    Args:
        agent: The Pepperpy agent to adapt
        **kwargs: Additional AutoGen-specific configuration
    """

    async def to_framework_agent(self) -> AutoGenAgent:
        """Convert Pepperpy agent to AutoGen agent.

        Returns:
            AutoGen agent instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            # Create a custom AutoGen agent class that wraps Pepperpy agent
            class PepperpyAutoGenAgent(ConversableAgent):
                def __init__(self, adapter: "AutoGenAdapter", **kwargs: Any) -> None:
                    super().__init__(**kwargs)
                    self._adapter = adapter

                async def receive(self, message: dict[str, Any], sender: Any) -> None:
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
            return PepperpyAutoGenAgent(self, name=self.agent.name)

        except Exception as e:
            raise ConversionError(f"Failed to convert to AutoGen agent: {e}") from e

    async def from_framework_message(self, message: Any) -> Message:
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
                sender=str(message.get("sender", "autogen")),
                receiver=str(message.get("receiver", "pepperpy")),
                content={"text": str(message.get("content", ""))},
            )
        except Exception as e:
            raise ConversionError(f"Failed to convert from AutoGen message: {e}") from e

    async def to_framework_message(self, message: Message) -> dict[str, Any]:
        """Convert Pepperpy message to AutoGen message.

        Args:
            message: Pepperpy Message instance

        Returns:
            AutoGen message dict

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
            raise ConversionError(f"Failed to convert to AutoGen message: {e}") from e

    async def from_framework_response(self, response: Any) -> Response:
        """Convert AutoGen response to Pepperpy response.

        Args:
            response: AutoGen response

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
            raise ConversionError(
                f"Failed to convert from AutoGen response: {e}"
            ) from e

    async def to_framework_response(self, response: Response) -> dict[str, Any]:
        """Convert Pepperpy response to AutoGen response.

        Args:
            response: Pepperpy Response instance

        Returns:
            AutoGen response dict

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
            raise ConversionError(f"Failed to convert to AutoGen response: {e}") from e
