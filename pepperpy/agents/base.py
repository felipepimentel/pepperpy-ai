"""Base classes and interfaces for the agents module."""

from typing import Any, Dict, List, Optional, Protocol

from pepperpy.core import ValidationError
from pepperpy.llm import LLMProvider


class Message:
    """Message from an agent."""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class Memory(Protocol):
    """Interface for agent memory."""

    async def add_message(self, message: Message) -> None:
        """Add a message to memory.

        Args:
            message: The message to add.
        """
        ...

    async def get_messages(self) -> List[Message]:
        """Get all messages from memory.

        Returns:
            List of messages.
        """
        ...

    async def clear(self) -> None:
        """Clear all messages from memory."""
        ...


class Agent(Protocol):
    """Interface for an agent."""

    async def initialize(self) -> None:
        """Initialize the agent."""
        ...

    async def execute_task(self, task: str) -> List[Message]:
        """Execute a task and return the messages.

        Args:
            task: The task to execute.

        Returns:
            List of messages from the execution.
        """
        ...


class AgentGroup(Protocol):
    """Interface for a group of agents."""

    async def initialize(self) -> None:
        """Initialize the agent group."""
        ...

    async def execute_task(self, task: str) -> List[Message]:
        """Execute a task using the agent group.

        Args:
            task: The task to execute.

        Returns:
            List of messages from the execution.
        """
        ...


class AgentFactory:
    """Factory for creating agents and agent groups."""

    @classmethod
    def create_agent(
        cls, llm_provider: LLMProvider, memory: Optional[Memory] = None
    ) -> Agent:
        """Create an agent with the given LLM provider and memory.

        Args:
            llm_provider: The LLM provider to use.
            memory: Optional memory implementation.

        Returns:
            An initialized agent.

        Raises:
            ValidationError: If the LLM provider is not properly configured.
        """
        from .providers.autogen import AutoGenAgent

        if not llm_provider.api_key:
            raise ValidationError("LLM provider requires an API key")

        return AutoGenAgent(llm_provider=llm_provider, memory=memory)

    @classmethod
    def create_group(
        cls,
        llm_provider: LLMProvider,
        group_config: Dict[str, Any],
        memory: Optional[Memory] = None,
    ) -> AgentGroup:
        """Create an agent group with the given configuration.

        Args:
            llm_provider: The LLM provider to use.
            group_config: Configuration for the agent group.
            memory: Optional memory implementation.

        Returns:
            An initialized agent group.

        Raises:
            ValidationError: If the configuration is invalid.
        """
        from .providers.autogen import AutoGenGroup

        if not llm_provider.api_key:
            raise ValidationError("LLM provider requires an API key")

        return AutoGenGroup(
            llm_provider=llm_provider, group_config=group_config, memory=memory
        )
