"""Base classes and protocols for the Pepperpy framework.

This module provides the foundational classes and protocols that define
the core functionality of the framework, including:

- BaseAgent: Abstract base class for all agents
- BaseProvider: Abstract base class for providers
- BaseMemoryStore: Abstract base class for memory stores
- BasePromptTemplate: Abstract base class for prompt templates
"""

import logging
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Protocol,
    Set,
    Type,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

from pepperpy.core.errors import ConfigurationError, StateError
from pepperpy.core.types import (
    AgentConfig,
    Message,
    MessageContent,
    MessageType,
    Response,
    ResponseStatus,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from enum import Enum
from typing import (
    ClassVar,
    TypedDict,
    TypeVar,
)

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class AgentState(str, Enum):
    r"""Possible states of an agent.

    The state machine follows these transitions:
    CREATED -> INITIALIZING -> READY -> PROCESSING -> READY
                                   \-> ERROR -> READY
                                   \-> CLEANING -> TERMINATED
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    CLEANING = "cleaning"
    TERMINATED = "terminated"

    def can_transition_to(self, target: "AgentState") -> bool:
        """Check if a state transition is valid.

        Args:
        ----
            target: The target state to transition to

        Returns:
        -------
            bool: Whether the transition is valid

        """
        transitions: dict[AgentState, set[AgentState]] = {
            AgentState.CREATED: {AgentState.INITIALIZING},
            AgentState.INITIALIZING: {AgentState.READY, AgentState.ERROR},
            AgentState.READY: {
                AgentState.PROCESSING,
                AgentState.CLEANING,
                AgentState.ERROR,
            },
            AgentState.PROCESSING: {AgentState.READY, AgentState.ERROR},
            AgentState.ERROR: {AgentState.READY, AgentState.CLEANING},
            AgentState.CLEANING: {AgentState.TERMINATED},
            AgentState.TERMINATED: set(),
        }
        return target in transitions[self]


# Define a TypedDict for metadata
class AgentMetadata(TypedDict, total=False):
    """Type definition for agent metadata."""

    name: str
    description: str
    tags: list[str]
    custom_data: dict[str, str | int | float | bool | None]


class AgentContext(BaseModel):
    """Context information for agent execution.

    This class maintains the execution context of an agent, including its
    identifiers, state, and metadata.

    Attributes
    ----------
        agent_id: Unique identifier for the agent
        session_id: Current session identifier
        memory_id: Optional memory context identifier
        metadata: Additional context information
        state: Current agent state
        parent_id: Optional parent agent identifier
        created_at: Creation timestamp
        updated_at: Last update timestamp

    """

    agent_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(default_factory=uuid4)
    memory_id: UUID | None = None
    metadata: AgentMetadata = Field(
        default_factory=lambda: AgentMetadata(
            name="",
            description="",
            tags=[],
            custom_data={},
        )
    )
    state: AgentState = Field(default=AgentState.CREATED)
    parent_id: UUID | None = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    class Config:
        """Pydantic model configuration."""

        frozen = True
        json_encoders: ClassVar[dict[type, Callable[..., str]]] = {
            UUID: str,
            AgentState: str,
        }

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: AgentMetadata) -> AgentMetadata:
        """Validate metadata dictionary."""
        return v.copy()

    @field_validator("updated_at")
    @classmethod
    def validate_timestamps(cls, v: float, info: ValidationInfo) -> float:
        """Validate that updated_at is not before created_at."""
        if "created_at" in info.data and v < info.data["created_at"]:
            raise ValueError("updated_at cannot be before created_at")
        return v

    def with_updates(
        self,
        **updates: str | int | float | bool | UUID | AgentState | AgentMetadata | None,
    ) -> "AgentContext":
        """Create a new context with updated values.

        Args:
        ----
            **updates: Values to update in the context. Valid types are:
                     - str: For string values
                     - int: For integer values
                     - float: For float values
                     - bool: For boolean values
                     - UUID: For UUID values
                     - AgentState: For state values
                     - AgentMetadata: For metadata updates
                     - None: For optional fields

        Returns:
        -------
            A new AgentContext instance with updated values

        """
        data = self.model_dump()
        data.update(updates)
        if "updated_at" not in updates:
            data["updated_at"] = time.time()
        return AgentContext(**data)


@dataclass
class AgentConfig:
    """Configuration for creating an agent."""

    type: str
    name: str
    description: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Type variables for generic agent types
T_Input_contra = TypeVar("T_Input_contra", contravariant=True)
T_Output_co = TypeVar("T_Output_co", covariant=True)
T_Config_contra = TypeVar(
    "T_Config_contra", bound=Mapping[str, Any], contravariant=True
)
T_Context_contra = TypeVar("T_Context_contra", contravariant=True)

# Regular type variables for the base agent implementation
T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")
T_Config = TypeVar("T_Config", bound=Mapping[str, Any])
T_Context = TypeVar("T_Context")

# Type alias for agent lifecycle callbacks
AgentCallback = Callable[[UUID, "AgentState"], Awaitable[None]]


@runtime_checkable
class AgentCapability(Protocol):
    """Protocol defining agent capabilities.

    This protocol defines the interface that all agent capabilities must
    implement. Capabilities provide additional functionality to agents.

    Attributes
    ----------
        name: Capability name
        version: Capability version
        description: Capability description
        requirements: Required dependencies

    """

    name: str
    version: str
    description: str
    requirements: list[str]

    def is_available(self) -> bool:
        """Check if the capability is available in current environment."""
        ...

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the capability with configuration.

        Args:
        ----
            config: Configuration parameters for the capability

        Raises:
        ------
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails

        """
        ...

    async def cleanup(self) -> None:
        """Cleanup capability resources.

        This method should release any resources held by the capability.
        """
        ...

    @property
    def is_initialized(self) -> bool:
        """Check if the capability is initialized."""
        ...


@runtime_checkable
class AgentProtocol(
    Protocol[T_Input_contra, T_Output_co, T_Config_contra, T_Context_contra]
):
    """Protocol defining the interface for Pepperpy agents.

    This protocol defines the core interface that all Pepperpy agents must
    implement. It provides methods for initialization, processing, and cleanup.

    Type Parameters:
        T_Input_contra: Type of input data (contravariant)
        T_Output_co: Type of output data (covariant)
        T_Config_contra: Type of configuration data (contravariant)
        T_Context_contra: Type of context data (contravariant)
    """

    @property
    @abstractmethod
    def id(self) -> UUID:
        """Unique identifier for the agent."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for the agent."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description of the agent's purpose and capabilities."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Agent version string."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """List of capabilities this agent supports."""
        pass

    @property
    @abstractmethod
    def state(self) -> AgentState:
        """Current state of the agent."""
        pass

    @property
    @abstractmethod
    def context(self) -> AgentContext:
        """Current agent context."""
        pass

    @abstractmethod
    async def initialize(self, config: T_Config_contra) -> None:
        """Initialize the agent with configuration.

        Args:
        ----
            config: Agent configuration

        Raises:
        ------
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails
            TimeoutError: If initialization times out

        """
        pass

    @abstractmethod
    async def process(
        self,
        input_data: T_Input_contra,
        context: T_Context_contra | None = None,
    ) -> T_Output_co:
        """Process input data and return results.

        Args:
        ----
            input_data: Data to process
            context: Optional processing context

        Returns:
        -------
            Processing results

        Raises:
        ------
            ValueError: If input data is invalid
            RuntimeError: If processing fails
            TimeoutError: If processing times out

        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the agent.

        This method should release any resources held by the agent.

        Raises
        ------
            RuntimeError: If cleanup fails

        """
        pass

    @abstractmethod
    def add_lifecycle_hook(
        self,
        state: AgentState,
        callback: AgentCallback,
    ) -> None:
        """Add a lifecycle hook for state changes."""
        pass

    @abstractmethod
    def remove_lifecycle_hook(
        self,
        state: AgentState,
        callback: AgentCallback,
    ) -> None:
        """Remove a lifecycle hook."""
        pass

    @abstractmethod
    async def validate_state_transition(self, target_state: AgentState) -> None:
        """Validate a state transition.

        Args:
        ----
            target_state: The target state

        Raises:
        ------
            ValueError: If the transition is invalid

        """
        pass

    @abstractmethod
    async def handle_error(self, error: Exception) -> None:
        """Handle an error that occurred during agent operation.

        Args:
        ----
            error: The error that occurred

        This method should:
        1. Log the error appropriately
        2. Update agent state
        3. Trigger error hooks
        4. Clean up resources if necessary

        """
        pass


class BaseAgent:
    """Base class for all agents.

    This class defines the core functionality that all agents must implement.
    It provides methods for initialization, message processing, and cleanup.
    """

    name: str
    description: str
    version: str
    capabilities: Set[str]
    _client: "PepperpyClientProtocol"
    _config: AgentConfig
    _context: AgentContext
    _initialized: bool

    def __init__(
        self,
        client: "PepperpyClientProtocol",
        config: AgentConfig,
    ) -> None:
        """Initialize the agent.

        Args:
            client: The Pepperpy client instance
            config: Agent configuration

        Raises:
            ConfigurationError: If configuration is invalid

        """
        if not config.type:
            raise ConfigurationError("Agent type must be specified")

        self.name = config.name
        self.description = config.description
        self.version = config.version
        self.capabilities = set(config.capabilities)
        self._client = client
        self._config = config
        self._initialized = False
        self._state = AgentState.CREATED

        logger.info(
            "Created agent %s (type=%s, version=%s)",
            self.name,
            config.type,
            self.version,
        )

    async def initialize(self) -> None:
        """Initialize the agent.

        This method should be called after instantiation to set up any
        resources needed by the agent.

        Raises:
            StateError: If agent is already initialized
            ConfigurationError: If initialization fails

        """
        if self._initialized:
            raise StateError("Agent is already initialized")

        try:
            self._state = AgentState.INITIALIZING
            # Initialize capabilities
            for capability in self.capabilities:
                logger.debug("Initializing capability %s", capability)
                # Initialize capability here

            self._initialized = True
            self._state = AgentState.READY
            logger.info("Agent %s initialized successfully", self.name)

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to initialize agent %s: %s", self.name, e)
            raise ConfigurationError(f"Failed to initialize agent: {e}") from e

    async def cleanup(self) -> None:
        """Clean up agent resources.

        This method should be called when the agent is no longer needed
        to clean up any resources.

        Raises:
            StateError: If agent is not initialized

        """
        if not self._initialized:
            raise StateError("Agent is not initialized")

        try:
            self._state = AgentState.CLEANING
            # Cleanup capabilities
            for capability in self.capabilities:
                logger.debug("Cleaning up capability %s", capability)
                # Cleanup capability here

            self._initialized = False
            self._state = AgentState.TERMINATED
            logger.info("Agent %s cleaned up successfully", self.name)

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to clean up agent %s: %s", self.name, e)
            raise StateError(f"Failed to clean up agent: {e}") from e

    async def process_message(self, message: Message) -> Response:
        """Process an incoming message.

        Args:
            message: The message to process

        Returns:
            The response to the message

        Raises:
            StateError: If agent is not initialized

        """
        if not self._initialized:
            raise StateError("Agent is not initialized")

        try:
            self._state = AgentState.PROCESSING
            logger.debug("Processing message: %s", message)

            # Default implementation just echoes the message
            response = Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.RESPONSE,
                    content={"text": f"Echo: {message.content}"},
                ),
                status=ResponseStatus.SUCCESS,
            )

            self._state = AgentState.READY
            return response

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to process message: %s", e)
            return Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.RESPONSE,
                    content={"error": str(e)},
                ),
                status=ResponseStatus.ERROR,
            )

    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized.

        Returns:
            True if initialized, False otherwise

        """
        return self._initialized

    @property
    def state(self) -> AgentState:
        """Get the current agent state.

        Returns:
            The current agent state

        """
        return self._state

    def add_capability(self, capability: Type[AgentCapability]) -> None:
        """Add a capability to the agent.

        Args:
            capability: The capability class to add

        Raises:
            StateError: If agent is already initialized
            ValueError: If capability is invalid

        """
        if self._initialized:
            raise StateError("Cannot add capability after initialization")

        if not hasattr(capability, "name"):
            raise ValueError("Capability must have a name attribute")

        self.capabilities.add(capability.name)
        logger.debug("Added capability %s to agent %s", capability.name, self.name)

    def remove_capability(self, capability_name: str) -> None:
        """Remove a capability from the agent.

        Args:
            capability_name: Name of capability to remove

        Raises:
            StateError: If agent is already initialized
            ValueError: If capability not found

        """
        if self._initialized:
            raise StateError("Cannot remove capability after initialization")

        if capability_name not in self.capabilities:
            raise ValueError(f"Capability {capability_name} not found")

        self.capabilities.remove(capability_name)
        logger.debug("Removed capability %s from agent %s", capability_name, self.name)

    def has_capability(self, capability_name: str) -> bool:
        """Check if agent has a capability.

        Args:
            capability_name: Name of capability to check

        Returns:
            True if agent has capability, False otherwise

        """
        return capability_name in self.capabilities


class AgentFactory(ABC):
    """Factory for creating agents."""

    @abstractmethod
    async def create_agent(
        self,
        agent_type: str,
        context: AgentContext,
        config: AgentConfig | None = None,
    ) -> BaseAgent:
        """Create a new agent instance.

        Args:
        ----
            agent_type: Type of agent to create
            context: Agent context
            config: Optional configuration

        Returns:
        -------
            BaseAgent: New agent instance

        """
        pass


class PepperpyClientProtocol(Protocol):
    """Protocol defining the interface for PepperpyClient."""

    async def send_message(self, message: str) -> str:
        """Send a message and get a response."""
        ...

    async def get_agent(self, agent_type: str) -> Any:
        """Get an agent instance."""
        ...


class Agent(BaseAgent):
    """Base implementation of the BaseAgent protocol.

    This class provides a default implementation of the BaseAgent protocol
    that can be extended by concrete agent implementations.
    """

    async def initialize(self) -> None:
        """Initialize the agent.

        This method should be called after instantiation to set up any
        resources needed by the agent.

        Raises
        ------
            StateError: If agent is already initialized
            ConfigurationError: If initialization fails

        """
        if self._initialized:
            raise StateError("Agent is already initialized")

        try:
            self._state = AgentState.INITIALIZING
            # Initialize capabilities
            for capability in self.capabilities:
                logger.debug("Initializing capability %s", capability)
                # Initialize capability here

            self._initialized = True
            self._state = AgentState.READY
            logger.info("Agent %s initialized successfully", self.name)

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to initialize agent %s: %s", self.name, e)
            raise ConfigurationError(f"Failed to initialize agent: {e}") from e

    async def cleanup(self) -> None:
        """Clean up agent resources.

        This method should be called when the agent is no longer needed
        to clean up any resources.

        Raises
        ------
            StateError: If agent is not initialized

        """
        if not self._initialized:
            raise StateError("Agent is not initialized")

        try:
            self._state = AgentState.CLEANING
            # Cleanup capabilities
            for capability in self.capabilities:
                logger.debug("Cleaning up capability %s", capability)
                # Cleanup capability here

            self._initialized = False
            self._state = AgentState.TERMINATED
            logger.info("Agent %s cleaned up successfully", self.name)

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to clean up agent %s: %s", self.name, e)
            raise StateError(f"Failed to clean up agent: {e}") from e

    async def process_message(self, message: Message) -> Response:
        """Process an incoming message.

        Args:
        ----
            message: The message to process

        Returns:
        -------
            The response to the message

        Raises:
        ------
            StateError: If agent is not initialized

        """
        if not self._initialized:
            raise StateError("Agent is not initialized")

        try:
            self._state = AgentState.PROCESSING
            logger.debug("Processing message: %s", message)

            # Default implementation just echoes the message
            response = Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.RESPONSE,
                    content={"text": f"Echo: {message.content}"},
                ),
                status=ResponseStatus.SUCCESS,
            )

            self._state = AgentState.READY
            return response

        except Exception as e:
            self._state = AgentState.ERROR
            logger.error("Failed to process message: %s", e)
            return Response(
                message_id=message.id,
                content=MessageContent(
                    type=MessageType.RESPONSE,
                    content={"error": str(e)},
                ),
                status=ResponseStatus.ERROR,
            )
