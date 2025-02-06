"""Runtime agent lifecycle management.

This module provides lifecycle management for runtime agents, handling state
transitions, resource cleanup, and error recovery.
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

from pepperpy.common.errors import LifecycleError
from pepperpy.core.types import AgentState
from pepperpy.monitoring.logger import get_logger
from pepperpy.runtime.context import ExecutionContext

logger = get_logger(__name__)


class LifecycleManager:
    """Manages the lifecycle of runtime agents.

    Handles state transitions, resource cleanup, error recovery,
    and monitoring integration.
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._contexts: dict[UUID, ExecutionContext] = {}
        self._state_handlers: dict[AgentState, dict[str, Callable]] = {}
        self._cleanup_handlers: dict[str, Callable] = {}
        self._error_handlers: dict[str, Callable] = {}

    def register_agent(self, context: ExecutionContext) -> None:
        """Register an agent for lifecycle management.

        Args:
            context: The agent's execution context

        Raises:
            LifecycleError: If the agent is already registered
        """
        if context.context_id in self._contexts:
            raise LifecycleError(f"Agent {context.context_id} already registered")

        self._contexts[context.context_id] = context
        logger.info(f"Registered agent {context.context_id} for lifecycle management")

    def transition_state(
        self, agent_id: UUID, target_state: AgentState, **kwargs: Any
    ) -> None:
        """Transition an agent to a new state.

        Args:
            agent_id: The UUID of the agent to transition
            target_state: The target state to transition to
            **kwargs: Additional arguments for state handlers

        Raises:
            LifecycleError: If the transition fails
        """
        try:
            context = self._get_context(agent_id)

            # Validate transition
            if not self._is_valid_transition(context.state, target_state):
                raise LifecycleError(
                    f"Invalid transition from {context.state} to {target_state}"
                )

            # Execute state handlers
            self._execute_state_handlers(context, target_state, **kwargs)

            # Update state
            context.set_state(target_state)
            logger.info(f"Transitioned agent {agent_id} to state {target_state}")

        except Exception as e:
            self._handle_error(agent_id, e)

    def cleanup_agent(self, agent_id: UUID) -> None:
        """Clean up agent resources.

        Args:
            agent_id: The UUID of the agent to clean up

        Raises:
            LifecycleError: If cleanup fails
        """
        try:
            context = self._get_context(agent_id)

            # Execute cleanup handlers
            for handler in self._cleanup_handlers.values():
                handler(context)

            # Remove context
            del self._contexts[agent_id]
            logger.info(f"Cleaned up agent {agent_id}")

        except Exception as e:
            self._handle_error(agent_id, e)

    def register_state_handler(
        self,
        state: AgentState,
        handler_id: str,
        handler: Callable[[ExecutionContext, Any], None],
    ) -> None:
        """Register a handler for state transitions.

        Args:
            state: The state to handle
            handler_id: Unique identifier for the handler
            handler: The handler function
        """
        if state not in self._state_handlers:
            self._state_handlers[state] = {}

        self._state_handlers[state][handler_id] = handler
        logger.debug(f"Registered state handler {handler_id} for state {state}")

    def register_cleanup_handler(
        self, handler_id: str, handler: Callable[[ExecutionContext], None]
    ) -> None:
        """Register a handler for agent cleanup.

        Args:
            handler_id: Unique identifier for the handler
            handler: The handler function
        """
        self._cleanup_handlers[handler_id] = handler
        logger.debug(f"Registered cleanup handler {handler_id}")

    def register_error_handler(
        self, handler_id: str, handler: Callable[[ExecutionContext, Exception], None]
    ) -> None:
        """Register a handler for error recovery.

        Args:
            handler_id: Unique identifier for the handler
            handler: The handler function
        """
        self._error_handlers[handler_id] = handler
        logger.debug(f"Registered error handler {handler_id}")

    def _get_context(self, agent_id: UUID) -> ExecutionContext:
        """Get an agent's execution context.

        Args:
            agent_id: The UUID of the agent

        Returns:
            The agent's execution context

        Raises:
            LifecycleError: If the agent is not found
        """
        if agent_id not in self._contexts:
            raise LifecycleError(f"Agent {agent_id} not found")

        return self._contexts[agent_id]

    def _is_valid_transition(
        self, current_state: AgentState, target_state: AgentState
    ) -> bool:
        """Check if a state transition is valid.

        Args:
            current_state: The current state
            target_state: The target state

        Returns:
            True if the transition is valid
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

        return target_state in valid_transitions.get(current_state, set())

    def _execute_state_handlers(
        self, context: ExecutionContext, target_state: AgentState, **kwargs: Any
    ) -> None:
        """Execute handlers for a state transition.

        Args:
            context: The agent's execution context
            target_state: The target state
            **kwargs: Additional arguments for handlers

        Raises:
            LifecycleError: If handler execution fails
        """
        try:
            handlers = self._state_handlers.get(target_state, {})
            for handler in handlers.values():
                handler(context, **kwargs)

        except Exception as e:
            raise LifecycleError(f"State handler execution failed: {e!s}") from e

    def _handle_error(self, agent_id: UUID, error: Exception) -> None:
        """Handle an error during lifecycle management.

        Args:
            agent_id: The UUID of the affected agent
            error: The error that occurred
        """
        try:
            context = self._get_context(agent_id)

            # Execute error handlers
            for handler in self._error_handlers.values():
                try:
                    handler(context, error)
                except Exception as e:
                    logger.error(
                        f"Error handler failed for agent {agent_id}: {e!s}",
                        exc_info=True,
                    )

            # Transition to error state
            context.set_state(AgentState.ERROR)
            logger.error(f"Agent {agent_id} transitioned to error state: {error!s}")

        except Exception as e:
            logger.critical(
                f"Failed to handle error for agent {agent_id}: {e!s}", exc_info=True
            )
