"""Runtime execution context management.

This module provides the execution context for agents, managing state, resources,
and monitoring throughout the agent's lifecycle.
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from pepperpy.common.errors import ContextError
from pepperpy.core.types import AgentState, ResourceId
from pepperpy.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionContext:
    """Manages the execution context for an agent instance.

    Handles state tracking, resource management, and monitoring integration
    for agent execution.

    Attributes:
        context_id: Unique identifier for this context
        agent_id: ID of the agent this context belongs to
        state: Current execution state
        resources: Mapping of resource IDs to their handlers
        metadata: Additional context metadata
    """

    context_id: UUID = field(default_factory=uuid4)
    agent_id: UUID | None = None
    state: AgentState = AgentState.INITIALIZED
    resources: dict[ResourceId, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize logging and monitoring."""
        logger.info(f"Created execution context {self.context_id}")

    def set_state(self, new_state: AgentState) -> None:
        """Update the context state with validation.

        Args:
            new_state: The new state to transition to

        Raises:
            ContextError: If the state transition is invalid
        """
        if not self._is_valid_transition(new_state):
            raise ContextError(
                f"Invalid state transition from {self.state} to {new_state}"
            )

        logger.debug(
            f"Context {self.context_id} state change: {self.state} -> {new_state}"
        )
        self.state = new_state

    def add_resource(self, resource_id: ResourceId, handler: Any) -> None:
        """Register a resource handler with this context.

        Args:
            resource_id: Unique identifier for the resource
            handler: The resource handler to register

        Raises:
            ContextError: If the resource ID is already registered
        """
        if resource_id in self.resources:
            raise ContextError(f"Resource {resource_id} already registered")

        self.resources[resource_id] = handler
        logger.debug(f"Added resource {resource_id} to context {self.context_id}")

    def get_resource(self, resource_id: ResourceId) -> Any:
        """Retrieve a registered resource handler.

        Args:
            resource_id: ID of the resource to retrieve

        Returns:
            The requested resource handler

        Raises:
            ContextError: If the resource is not found
        """
        if resource_id not in self.resources:
            raise ContextError(f"Resource {resource_id} not found")

        return self.resources[resource_id]

    def remove_resource(self, resource_id: ResourceId) -> None:
        """Remove a registered resource.

        Args:
            resource_id: ID of the resource to remove

        Raises:
            ContextError: If the resource is not found
        """
        if resource_id not in self.resources:
            raise ContextError(f"Resource {resource_id} not found")

        del self.resources[resource_id]
        logger.debug(f"Removed resource {resource_id} from context {self.context_id}")

    def _is_valid_transition(self, new_state: AgentState) -> bool:
        """Check if a state transition is valid.

        Args:
            new_state: The proposed new state

        Returns:
            True if the transition is valid, False otherwise
        """
        # Define valid state transitions
        valid_transitions = {
            AgentState.INITIALIZED: {AgentState.STARTING, AgentState.ERROR},
            AgentState.STARTING: {AgentState.RUNNING, AgentState.ERROR},
            AgentState.RUNNING: {
                AgentState.PAUSED,
                AgentState.STOPPING,
                AgentState.ERROR,
            },
            AgentState.PAUSED: {
                AgentState.RUNNING,
                AgentState.STOPPING,
                AgentState.ERROR,
            },
            AgentState.STOPPING: {AgentState.STOPPED, AgentState.ERROR},
            AgentState.STOPPED: {AgentState.STARTING, AgentState.ERROR},
            AgentState.ERROR: {AgentState.STARTING, AgentState.STOPPED},
        }

        return new_state in valid_transitions.get(self.state, set())
