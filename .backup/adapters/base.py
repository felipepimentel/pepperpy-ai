"""Framework adapter base interface.

This module defines the base interface for framework adapters.
Framework adapters allow Pepperpy to integrate with different AI agent frameworks
like LangChain, AutoGen, Semantic Kernel, and CrewAI.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Generic, Protocol, TypeVar

from pepperpy.core.base import AgentProtocol
from pepperpy.core.types import Message, Response

# Type variables for framework-specific types
T = TypeVar("T")  # Framework agent type
M = TypeVar("M")  # Framework message type
R = TypeVar("R")  # Framework response type

# Type aliases for configuration values
ConfigValue = str | int | float | bool | dict[str, "ConfigValue"] | None
ConfigDict = dict[str, ConfigValue]


class FrameworkConfig(Protocol):
    """Protocol for framework-specific configuration."""

    def __getitem__(self, key: str) -> ConfigValue:
        """Get configuration value."""
        ...


class BaseFrameworkAdapter(Generic[T, M, R], ABC):
    """Base class for framework adapters.

    Framework adapters provide a bridge between Pepperpy's agent system
    and external frameworks like LangChain, AutoGen, etc.

    Args:
        agent: The Pepperpy agent to adapt
        **kwargs: Additional framework-specific configuration
    """

    def __init__(
        self,
        agent: AgentProtocol[Message, Response, Mapping[str, ConfigValue], Message],
        **kwargs: ConfigValue,
    ) -> None:
        """Initialize the adapter.

        Args:
            agent: The Pepperpy agent to adapt
            **kwargs: Additional framework-specific configuration
        """
        self.agent = agent
        self.config: ConfigDict = kwargs

    @abstractmethod
    async def to_framework_agent(self) -> T:
        """Convert Pepperpy agent to framework-specific agent.

        Returns:
            The framework-specific agent instance

        Raises:
            AdapterError: If conversion fails
        """
        pass

    @abstractmethod
    async def from_framework_message(self, message: M) -> Message:
        """Convert framework message to Pepperpy message.

        Args:
            message: Framework-specific message

        Returns:
            Pepperpy Message instance

        Raises:
            AdapterError: If conversion fails
        """
        pass

    @abstractmethod
    async def to_framework_message(self, message: Message) -> M:
        """Convert Pepperpy message to framework message.

        Args:
            message: Pepperpy Message instance

        Returns:
            Framework-specific message

        Raises:
            AdapterError: If conversion fails
        """
        pass

    @abstractmethod
    async def from_framework_response(self, response: R) -> Response:
        """Convert framework response to Pepperpy response.

        Args:
            response: Framework-specific response

        Returns:
            Pepperpy Response instance

        Raises:
            AdapterError: If conversion fails
        """
        pass

    @abstractmethod
    async def to_framework_response(self, response: Response) -> R:
        """Convert Pepperpy response to framework response.

        Args:
            response: Pepperpy Response instance

        Returns:
            Framework-specific response

        Raises:
            AdapterError: If conversion fails
        """
        pass
