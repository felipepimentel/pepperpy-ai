"""LangChain framework adapter.

This module implements the adapter for the LangChain framework.
"""

from typing import Any
from uuid import uuid4

from langchain.agents import AgentExecutor, BaseAgent
from langchain.schema import AgentAction, AgentFinish

from pepperpy.adapters.base import BaseFrameworkAdapter
from pepperpy.adapters.errors import ConversionError
from pepperpy.core.types import Message, MessageType, Response, ResponseStatus


class LangChainAdapter(BaseFrameworkAdapter[AgentExecutor]):
    """Adapter for LangChain framework.

    This adapter allows Pepperpy agents to be used as LangChain agents
    and vice versa.

    Args:
        agent: The Pepperpy agent to adapt
        **kwargs: Additional LangChain-specific configuration
    """

    async def to_framework_agent(self) -> AgentExecutor:
        """Convert Pepperpy agent to LangChain agent.

        Returns:
            LangChain AgentExecutor instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            # Create LangChain agent class
            class PepperpyLangChainAgent(BaseAgent):
                def plan(
                    self,
                    intermediate_steps: list[tuple[AgentAction, str]],
                    **kwargs: Any,
                ) -> AgentAction | AgentFinish:
                    """Plan next action using Pepperpy agent."""
                    # Convert intermediate steps to Pepperpy messages
                    messages = [
                        self._adapter.from_framework_message(step)
                        for step in intermediate_steps
                    ]

                    # Get response from Pepperpy agent
                    response = self._adapter.agent.process_messages(messages)

                    # Convert response to LangChain format
                    return self._adapter.to_framework_response(response)

            # Create agent instance
            lc_agent = PepperpyLangChainAgent()
            lc_agent._adapter = self

            # Create executor
            return AgentExecutor.from_agent_and_tools(
                agent=lc_agent,
                tools=self.config.get("tools", []),
                verbose=self.config.get("verbose", False),
            )

        except Exception as e:
            raise ConversionError(f"Failed to convert to LangChain agent: {e}") from e

    async def from_framework_message(self, message: Any) -> Message:
        """Convert LangChain message to Pepperpy message.

        Args:
            message: LangChain message (AgentAction or str)

        Returns:
            Pepperpy Message instance

        Raises:
            ConversionError: If conversion fails
        """
        try:
            if isinstance(message, tuple):
                action, observation = message
                # Convert to Pepperpy message
                return Message(
                    id=uuid4(),
                    type=MessageType.COMMAND,
                    sender="pepperpy",
                    receiver="langchain",
                    content={"action": action.tool, "input": action.tool_input},
                    metadata={"original": action.dict()},
                )
            elif isinstance(message, str):
                return Message(
                    id=uuid4(),
                    type=MessageType.RESPONSE,
                    sender="pepperpy",
                    receiver="langchain",
                    content={"output": message},
                    metadata={},
                )
            else:
                raise ConversionError(f"Unsupported message type: {type(message)}")

        except Exception as e:
            raise ConversionError(
                f"Failed to convert from LangChain message: {e}"
            ) from e

    async def to_framework_message(self, message: Message) -> AgentAction:
        """Convert Pepperpy message to LangChain message.

        Args:
            message: Pepperpy Message instance

        Returns:
            LangChain AgentAction

        Raises:
            ConversionError: If conversion fails
        """
        try:
            content = message.content
            return AgentAction(
                tool=content.get("action", "default"),
                tool_input=content.get("input", ""),
                log=str(content),
            )

        except Exception as e:
            raise ConversionError(f"Failed to convert to LangChain message: {e}") from e

    async def from_framework_response(self, response: Any) -> Response:
        """Convert a LangChain AgentFinish to a Pepperpy response."""
        if not isinstance(response, AgentFinish):
            raise ConversionError(f"Unsupported response type: {type(response)}")

        return Response(
            id=uuid4(),
            message_id=uuid4(),  # Since we don't have the original message ID
            status=ResponseStatus.SUCCESS,
            content={"output": response.return_values.get("output", "")},
            metadata={"original": response.dict()},
        )

    async def to_framework_response(self, response: Response) -> AgentFinish:
        """Convert a Pepperpy response to a LangChain AgentFinish."""
        return AgentFinish(
            return_values={"output": response.content.get("output", "")},
            log=str(response.metadata.get("log", "")),
        )
