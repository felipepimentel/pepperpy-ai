"""Lifecycle management for Pepperpy components.

This module provides lifecycle management for components, including:
- Component registration and initialization
- State transitions and validation
- Cleanup and resource management
"""

import asyncio
import logging
from collections import defaultdict
from enum import Enum, auto
from typing import Any, Callable, TypeVar
from uuid import UUID, uuid4

from pepperpy.core.errors import LifecycleError, StateError
from pepperpy.monitoring.logger import structured_logger

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Component type


class ComponentState(Enum):
    """States that a component can be in."""

    UNREGISTERED = auto()
    REGISTERED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    ERROR = auto()
    TERMINATED = auto()


class LifecycleManager:
    """Manages component lifecycle states and transitions.

    This class handles:
    - Component registration and tracking
    - State transitions and validation
    - Dependency management
    - Error handling and recovery
    """

    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._components: dict[UUID, Any] = {}
        self._states: dict[UUID, ComponentState] = {}
        self._dependencies: dict[UUID, set[UUID]] = defaultdict(set)
        self._handlers: dict[ComponentState, set[Callable]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._logger = structured_logger

    def _validate_transition(
        self,
        component_id: UUID,
        current_state: ComponentState,
        target_state: ComponentState,
    ) -> None:
        """Validate a state transition.

        Args:
            component_id: Component identifier
            current_state: Current state
            target_state: Target state

        Raises:
            StateError: If transition is invalid
        """
        valid_transitions = {
            ComponentState.UNREGISTERED: {ComponentState.REGISTERED},
            ComponentState.REGISTERED: {
                ComponentState.INITIALIZING,
                ComponentState.ERROR,
                ComponentState.TERMINATED,
            },
            ComponentState.INITIALIZING: {
                ComponentState.INITIALIZED,
                ComponentState.ERROR,
            },
            ComponentState.INITIALIZED: {
                ComponentState.STARTING,
                ComponentState.ERROR,
                ComponentState.TERMINATED,
            },
            ComponentState.STARTING: {
                ComponentState.RUNNING,
                ComponentState.ERROR,
            },
            ComponentState.RUNNING: {
                ComponentState.STOPPING,
                ComponentState.ERROR,
            },
            ComponentState.STOPPING: {
                ComponentState.STOPPED,
                ComponentState.ERROR,
            },
            ComponentState.STOPPED: {
                ComponentState.STARTING,
                ComponentState.TERMINATED,
                ComponentState.ERROR,
            },
            ComponentState.ERROR: {
                ComponentState.INITIALIZING,
                ComponentState.TERMINATED,
            },
            ComponentState.TERMINATED: set(),
        }

        if target_state not in valid_transitions[current_state]:
            raise StateError(
                f"Invalid transition from {current_state} to {target_state}",
                current_state=current_state.name,
                expected_state=target_state.name,
                details={"component_id": str(component_id)},
            )

    async def _update_state(
        self,
        component_id: UUID,
        target_state: ComponentState,
    ) -> None:
        """Update component state with validation.

        Args:
            component_id: Component identifier
            target_state: Target state

        Raises:
            StateError: If state transition is invalid
            LifecycleError: If state update fails
        """
        async with self._lock:
            try:
                current_state = self._states[component_id]
                self._validate_transition(component_id, current_state, target_state)
                self._states[component_id] = target_state

                # Trigger state change handlers
                handlers = self._handlers[target_state]
                for handler in handlers:
                    try:
                        handler(component_id)
                    except Exception as e:
                        self._logger.error(
                            "State change handler failed",
                            component_id=str(component_id),
                            state=target_state.name,
                            error=str(e),
                        )

            except Exception as e:
                raise LifecycleError(
                    f"Failed to update state: {e}",
                    component=str(component_id),
                    state=target_state.name,
                ) from e

    def register(self, component: Any) -> UUID:
        """Register a new component.

        Args:
            component: Component to register

        Returns:
            Component identifier

        Raises:
            LifecycleError: If registration fails
        """
        component_id = uuid4()
        try:
            self._components[component_id] = component
            self._states[component_id] = ComponentState.REGISTERED
            return component_id

        except Exception as e:
            raise LifecycleError(
                f"Failed to register component: {e}",
                component=str(component_id),
            ) from e

    async def initialize(self, component_id: UUID) -> None:
        """Initialize a component.

        Args:
            component_id: Component identifier

        Raises:
            StateError: If component is in invalid state
            LifecycleError: If initialization fails
        """
        try:
            component = self._components[component_id]
            await self._update_state(component_id, ComponentState.INITIALIZING)
            await component.initialize()
            await self._update_state(component_id, ComponentState.INITIALIZED)

        except Exception as e:
            await self._update_state(component_id, ComponentState.ERROR)
            raise LifecycleError(
                f"Failed to initialize component: {e}",
                component=str(component_id),
            ) from e

    async def start(self, component_id: UUID) -> None:
        """Start a component.

        Args:
            component_id: Component identifier

        Raises:
            StateError: If component is in invalid state
            LifecycleError: If start fails
        """
        try:
            component = self._components[component_id]
            await self._update_state(component_id, ComponentState.STARTING)
            await component.start()
            await self._update_state(component_id, ComponentState.RUNNING)

        except Exception as e:
            await self._update_state(component_id, ComponentState.ERROR)
            raise LifecycleError(
                f"Failed to start component: {e}",
                component=str(component_id),
            ) from e

    async def stop(self, component_id: UUID) -> None:
        """Stop a component.

        Args:
            component_id: Component identifier

        Raises:
            StateError: If component is in invalid state
            LifecycleError: If stop fails
        """
        try:
            component = self._components[component_id]
            await self._update_state(component_id, ComponentState.STOPPING)
            await component.stop()
            await self._update_state(component_id, ComponentState.STOPPED)

        except Exception as e:
            await self._update_state(component_id, ComponentState.ERROR)
            raise LifecycleError(
                f"Failed to stop component: {e}",
                component=str(component_id),
            ) from e

    async def terminate(self, component_id: UUID) -> None:
        """Terminate a component.

        Args:
            component_id: Component identifier

        Raises:
            StateError: If component is in invalid state
            LifecycleError: If termination fails
        """
        try:
            await self._update_state(component_id, ComponentState.TERMINATED)
            del self._components[component_id]
            del self._states[component_id]
            self._dependencies.pop(component_id, None)

        except Exception as e:
            raise LifecycleError(
                f"Failed to terminate component: {e}",
                component=str(component_id),
            ) from e

    def add_dependency(self, component_id: UUID, dependency_id: UUID) -> None:
        """Add a dependency between components.

        Args:
            component_id: Dependent component identifier
            dependency_id: Dependency component identifier

        Raises:
            LifecycleError: If dependency addition fails
        """
        try:
            if component_id not in self._components:
                raise ValueError(f"Component {component_id} not found")
            if dependency_id not in self._components:
                raise ValueError(f"Dependency {dependency_id} not found")
            self._dependencies[component_id].add(dependency_id)

        except Exception as e:
            raise LifecycleError(
                f"Failed to add dependency: {e}",
                component=str(component_id),
            ) from e

    def add_state_handler(
        self,
        state: ComponentState,
        handler: Callable[[UUID], None],
    ) -> None:
        """Add a handler for state changes.

        Args:
            state: State to handle
            handler: Handler function
        """
        self._handlers[state].add(handler)

    def remove_state_handler(
        self,
        state: ComponentState,
        handler: Callable[[UUID], None],
    ) -> None:
        """Remove a state change handler.

        Args:
            state: State to handle
            handler: Handler function
        """
        self._handlers[state].discard(handler)

    def get_state(self, component_id: UUID) -> ComponentState:
        """Get current state of a component.

        Args:
            component_id: Component identifier

        Returns:
            Current component state

        Raises:
            KeyError: If component not found
        """
        return self._states[component_id]

    def get_dependencies(self, component_id: UUID) -> set[UUID]:
        """Get dependencies of a component.

        Args:
            component_id: Component identifier

        Returns:
            Set of dependency identifiers
        """
        return self._dependencies[component_id].copy()

    def is_running(self, component_id: UUID) -> bool:
        """Check if a component is running.

        Args:
            component_id: Component identifier

        Returns:
            True if component is running
        """
        return self._states.get(component_id) == ComponentState.RUNNING
