"""Base agent implementation.

This module provides the base agent class that all agents must inherit from.
It defines the core functionality and interface that all Pepperpy agents
must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar
from uuid import UUID

from pepperpy.core.base import BaseComponent, Metadata
from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.logging import get_logger
from pepperpy.core.types import (
    AgentState,
    Message,
    Response,
)

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class AgentMessage:
    """Represents a message in agent communication."""

    role: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentAction:
    """Represents an action taken by an agent."""

    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentState:
    """Represents the current state of an agent."""

    messages: List[AgentMessage]
    actions: List[AgentAction]
    memory: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Base class for agents."""

    @abstractmethod
    async def process(
        self, message: str, *, state: Optional[AgentState] = None, **kwargs: Any
    ) -> AgentState:
        """Process a message and update agent state.

        Args:
            message: Input message to process
            state: Current agent state
            **kwargs: Additional processing parameters

        Returns:
            Updated agent state
        """
        pass

    @abstractmethod
    async def act(
        self, state: AgentState, *, action_type: Optional[str] = None, **kwargs: Any
    ) -> AgentAction:
        """Take an action based on current state.

        Args:
            state: Current agent state
            action_type: Type of action to take
            **kwargs: Additional action parameters

        Returns:
            Action taken by agent
        """
        pass

    @abstractmethod
    async def observe(
        self,
        action: AgentAction,
        result: Any,
        *,
        state: Optional[AgentState] = None,
        **kwargs: Any,
    ) -> AgentState:
        """Process action result and update state.

        Args:
            action: Action that was taken
            result: Result of the action
            state: Current agent state
            **kwargs: Additional observation parameters

        Returns:
            Updated agent state
        """
        pass


class BaseAgent(BaseComponent):
    """Base class for all Pepperpy agents.

    This class provides the foundation for building agents in the Pepperpy
    framework. It handles lifecycle management, state tracking, and basic
    agent functionality.

    Attributes:
        id: Unique identifier for the agent
        state: Current agent state
        metadata: Agent metadata
        config: Agent configuration
        capabilities: List of agent capabilities

    """

    def __init__(
        self,
        id: UUID,
        metadata: Optional[Metadata] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the base agent.

        Args:
            id: Unique identifier for the agent
            metadata: Optional agent metadata
            config: Optional agent configuration

        Raises:
            ConfigurationError: If configuration is invalid

        """
        super().__init__(id, metadata)
        self.config = config or {}
        self.state = AgentState.CREATED
        self._logger = logger.getChild(self.__class__.__name__)

    @property
    def capabilities(self) -> List[str]:
        """Get agent capabilities.

        Returns:
            List of capability identifiers

        """
        return []

    async def initialize(self) -> None:
        """Initialize the agent.

        This method is called during agent startup to perform any necessary
        initialization.

        Raises:
            StateError: If agent is in invalid state
            ConfigurationError: If initialization fails

        """
        if self.state != AgentState.CREATED:
            raise StateError(f"Cannot initialize agent in state: {self.state}")

        try:
            self.state = AgentState.INITIALIZING
            # Perform initialization
            self.state = AgentState.READY
        except Exception as e:
            self.state = AgentState.ERROR
            raise ConfigurationError(f"Agent initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up agent resources.

        This method is called during agent shutdown to perform cleanup.
        """
        if self.state not in {AgentState.READY, AgentState.ERROR}:
            raise StateError(f"Cannot cleanup agent in state: {self.state}")

        try:
            self.state = AgentState.CLEANING
            # Perform cleanup
            self.state = AgentState.TERMINATED
        except Exception as e:
            self.state = AgentState.ERROR
            raise StateError(f"Agent cleanup failed: {e}") from e

    @abstractmethod
    async def process_message(self, message: Message) -> Response:
        """Process an incoming message.

        This is the main entry point for agent message processing. All agents
        must implement this method to handle incoming messages.

        Args:
            message: The message to process

        Returns:
            Response containing processing results

        Raises:
            NotImplementedError: If not implemented by subclass

        """
        raise NotImplementedError

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the agent's main functionality.

        This method implements the BaseComponent interface. It processes
        a message if one is provided in kwargs.

        Args:
            **kwargs: Execution parameters

        Returns:
            Execution results

        Raises:
            StateError: If agent is in invalid state

        """
        if self.state != AgentState.READY:
            raise StateError(f"Cannot execute agent in state: {self.state}")

        message = kwargs.get("message")
        if not message:
            raise ConfigurationError("Message is required for execution")

        try:
            self.state = AgentState.PROCESSING
            response = await self.process_message(message)
            self.state = AgentState.READY
            return response
        except Exception as e:
            self.state = AgentState.ERROR
            raise StateError(f"Agent execution failed: {e}") from e

    def validate(self) -> None:
        """Validate agent state and configuration.

        Raises:
            StateError: If agent state is invalid
            ConfigurationError: If configuration is invalid

        """
        super().validate()
        if not isinstance(self.state, AgentState):
            raise StateError(f"Invalid agent state: {self.state}")
        if not isinstance(self.config, dict):
            raise ConfigurationError("Agent config must be a dictionary")
