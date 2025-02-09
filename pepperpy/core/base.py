"""Base interfaces and protocols for the Pepperpy system.

This module defines the core interfaces and base classes that form the foundation
of the Pepperpy system, including agent states, contexts, configurations, and
capability protocols.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Generic,
    Protocol,
    TypedDict,
    TypeVar,
    runtime_checkable,
)
from uuid import UUID, uuid4

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
            target: The target state to transition to

        Returns:
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

    Attributes:
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
            A new AgentContext instance with updated values
        """
        data = self.model_dump()
        data.update(updates)
        if "updated_at" not in updates:
            data["updated_at"] = time.time()
        return AgentContext(**data)


class AgentConfig(BaseModel):
    """Base configuration for agents.

    This class defines the basic configuration parameters that all agents
    must support.

    Attributes:
        name: Human-readable name for the agent
        description: Detailed description of the agent
        version: Semantic version string (MAJOR.MINOR.PATCH)
        capabilities: List of required capabilities
        settings: Additional configuration settings
        timeout: Operation timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
    """

    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    capabilities: list[str] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)
    timeout: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    retry_delay: float = Field(default=1.0, ge=0)

    class Config:
        """Pydantic model configuration."""

        extra = "forbid"
        json_encoders: ClassVar[dict[type, Callable[..., str]]] = {
            UUID: str,
        }

    @field_validator("settings")
    @classmethod
    def validate_settings(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure settings is immutable."""
        return dict(v)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        try:
            major, minor, patch = map(int, v.split("."))
            if major < 0 or minor < 0 or patch < 0:
                raise ValueError
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid semantic version format") from e
        return v


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

    Attributes:
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

    async def initialize(self, config: Mapping[str, Any]) -> None:
        """Initialize the capability with configuration.

        Args:
            config: Configuration parameters for the capability

        Raises:
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
            config: Agent configuration

        Raises:
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
            input_data: Data to process
            context: Optional processing context

        Returns:
            Processing results

        Raises:
            ValueError: If input data is invalid
            RuntimeError: If processing fails
            TimeoutError: If processing times out
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the agent.

        This method should release any resources held by the agent.

        Raises:
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
            target_state: The target state

        Raises:
            ValueError: If the transition is invalid
        """
        pass

    @abstractmethod
    async def handle_error(self, error: Exception) -> None:
        """Handle an error that occurred during agent operation.

        Args:
            error: The error that occurred

        This method should:
        1. Log the error appropriately
        2. Update agent state
        3. Trigger error hooks
        4. Clean up resources if necessary
        """
        pass


class BaseAgent(ABC, Generic[T_Input, T_Output, T_Config, T_Context]):
    """Base class for all Pepperpy agents.

    This class provides a foundation for implementing agents with common
    functionality like state management and lifecycle hooks.
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str,
        capabilities: list[str] | None = None,
        id: UUID | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            name: Human-readable name for the agent
            description: Detailed description of the agent
            version: Agent version string
            capabilities: List of required capabilities
            id: Optional unique identifier
        """
        self._id = id or uuid4()
        self._name = name
        self._description = description
        self._version = version
        self._capabilities = capabilities or []
        self._state = AgentState.CREATED
        self._context = AgentContext(agent_id=self._id)
        self._lifecycle_hooks: dict[AgentState, set[AgentCallback]] = {
            state: set() for state in AgentState
        }

    @property
    def id(self) -> UUID:
        """Get the agent's unique identifier."""
        return self._id

    @property
    def name(self) -> str:
        """Get the agent's name."""
        return self._name

    @property
    def description(self) -> str:
        """Get the agent's description."""
        return self._description

    @property
    def version(self) -> str:
        """Get the agent's version."""
        return self._version

    @property
    def capabilities(self) -> list[str]:
        """Get the agent's capabilities."""
        return self._capabilities.copy()

    @property
    def state(self) -> AgentState:
        """Get the agent's current state."""
        return self._state

    async def _update_state(self, new_state: AgentState) -> None:
        """Update the agent's state and trigger lifecycle hooks.

        Args:
            new_state: The new state to transition to
        """
        if not self._state.can_transition_to(new_state):
            raise ValueError(f"Invalid state transition: {self._state} -> {new_state}")

        self._state = new_state
        self._context = self._context.with_updates(state=new_state)

        # Trigger lifecycle hooks
        hooks = self._lifecycle_hooks[new_state]
        for hook in hooks:
            await hook(self.id, new_state)

    def add_lifecycle_hook(
        self,
        state: AgentState,
        callback: AgentCallback,
    ) -> None:
        """Add a lifecycle hook for state changes.

        Args:
            state: The state to hook into
            callback: The callback to execute
        """
        self._lifecycle_hooks[state].add(callback)

    def remove_lifecycle_hook(
        self,
        state: AgentState,
        callback: AgentCallback,
    ) -> None:
        """Remove a lifecycle hook.

        Args:
            state: The state to remove the hook from
            callback: The callback to remove
        """
        self._lifecycle_hooks[state].discard(callback)

    @abstractmethod
    async def initialize(self, config: T_Config) -> None:
        """Initialize the agent with configuration.

        Args:
            config: Agent configuration

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If initialization fails
            TimeoutError: If initialization times out
        """
        await self._update_state(AgentState.INITIALIZING)
        try:
            await self._initialize_impl(config)
            await self._update_state(AgentState.READY)
        except Exception as e:
            await self._update_state(AgentState.ERROR)
            raise e

    @abstractmethod
    async def _initialize_impl(self, config: T_Config) -> None:
        """Implementation of agent initialization.

        Args:
            config: Agent configuration
        """
        pass

    @abstractmethod
    async def process(
        self,
        input_data: T_Input,
        context: T_Context | None = None,
    ) -> T_Output:
        """Process input data and return results.

        Args:
            input_data: Data to process
            context: Optional processing context

        Returns:
            Processing results

        Raises:
            ValueError: If input data is invalid
            RuntimeError: If processing fails
            TimeoutError: If processing times out
        """
        if self._state != AgentState.READY:
            raise RuntimeError(
                f"Agent must be in READY state to process, current state: {self._state}"
            )

        await self._update_state(AgentState.PROCESSING)
        try:
            result = await self._process_impl(input_data, context)
            await self._update_state(AgentState.READY)
            return result
        except Exception as e:
            await self._update_state(AgentState.ERROR)
            raise e

    @abstractmethod
    async def _process_impl(
        self,
        input_data: T_Input,
        context: T_Context | None = None,
    ) -> T_Output:
        """Implementation of input processing.

        Args:
            input_data: Data to process
            context: Optional processing context

        Returns:
            Processing results
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the agent.

        This method should release any resources held by the agent.

        Raises:
            RuntimeError: If cleanup fails
        """
        await self._update_state(AgentState.CLEANING)
        try:
            await self._cleanup_impl()
            await self._update_state(AgentState.TERMINATED)
        except Exception as e:
            await self._update_state(AgentState.ERROR)
            raise e

    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """Implementation of resource cleanup."""
        pass


class AgentFactory(ABC):
    """Factory for creating agents."""

    @abstractmethod
    async def create_agent(
        self,
        agent_type: str,
        context: AgentContext,
        config: AgentConfig | None = None,
    ) -> BaseAgent[Any, Any, Any, Any]:
        """Create a new agent instance.

        Args:
            agent_type: Type of agent to create
            context: Agent context
            config: Optional configuration

        Returns:
            BaseAgent: New agent instance
        """
        pass
