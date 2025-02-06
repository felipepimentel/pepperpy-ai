"""Framework adapter base interface.

This module defines the base interface for framework adapters.
Framework adapters allow Pepperpy to integrate with different AI agent frameworks
like LangChain, AutoGen, Semantic Kernel, and CrewAI.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pepperpy.core.base import AgentProtocol
from pepperpy.core.types import Message, Response

# Type variable for framework-specific agent types
T = TypeVar("T")


class BaseFrameworkAdapter(Generic[T], ABC):
    """Base class for framework adapters.

    Framework adapters provide a bridge between Pepperpy's agent system
    and external frameworks like LangChain, AutoGen, etc.

    Args:
        agent: The Pepperpy agent to adapt
        **kwargs: Additional framework-specific configuration
    """

    def __init__(self, agent: AgentProtocol[Any, Any, Any, Any], **kwargs: Any) -> None:
        """Initialize the adapter.

        Args:
            agent: The Pepperpy agent to adapt
            **kwargs: Additional framework-specific configuration
        """
        self.agent = agent
        self.config = kwargs

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
    async def from_framework_message(self, message: Any) -> Message:
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
    async def to_framework_message(self, message: Message) -> Any:
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
    async def from_framework_response(self, response: Any) -> Response:
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
    async def to_framework_response(self, response: Response) -> Any:
        """Convert Pepperpy response to framework response.

        Args:
            response: Pepperpy Response instance

        Returns:
            Framework-specific response

        Raises:
            AdapterError: If conversion fails
        """
        pass
