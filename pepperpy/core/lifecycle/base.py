"""Base components for lifecycle management."""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set
from uuid import UUID, uuid4

from pepperpy.core.errors import LifecycleError, StateError

logger = logging.getLogger(__name__)


class ComponentState(Enum):
    """Possible states of a lifecycle-managed component."""

    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"


class Lifecycle(ABC):
    """Base interface for components with lifecycle management.

    This abstract class defines the interface that all lifecycle-managed components
    must implement. It provides basic state management and error tracking.

    Attributes:
        state (ComponentState): Current state of the component.
        error (Optional[Exception]): Last error encountered, if any.
        id (UUID): Unique identifier for the component.

    """

    def __init__(self) -> None:
        """Initialize a new lifecycle component."""
        self._state = ComponentState.UNREGISTERED
        self._error: Optional[Exception] = None
        self._metadata: Dict[str, Any] = {}
        self._id = uuid4()

    @property
    def state(self) -> ComponentState:
        """Get the current state of the component."""
        return self._state

    @property
    def error(self) -> Optional[Exception]:
        """Get the last error encountered by the component, if any."""
        return self._error

    @property
    def id(self) -> UUID:
        """Get the component's unique identifier."""
        return self._id

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should be implemented to perform any necessary setup
        or resource allocation for the component.

        Raises:
            Exception: If initialization fails.

        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up component resources.

        This method should be implemented to perform any necessary cleanup
        or resource deallocation for the component.

        Raises:
            Exception: If cleanup fails.

        """
        pass

    async def start(self) -> None:
        """Start the component.

        This method can be overridden to implement startup logic.
        The default implementation does nothing.

        Raises:
            Exception: If startup fails.

        """
        pass

    async def stop(self) -> None:
        """Stop the component.

        This method can be overridden to implement shutdown logic.
        The default implementation does nothing.

        Raises:
            Exception: If shutdown fails.

        """
        pass


class LifecycleManager:
    """Central manager for lifecycle-managed components.

    This class manages the lifecycle of multiple components, handling their
    initialization, state tracking, and cleanup in a coordinated way.

    Features:
    - Component registration and tracking
    - State transitions and validation
    - Dependency management
    - Error handling and recovery
    - State change notifications
    """

    def __init__(self) -> None:
        """Initialize a new lifecycle manager."""
        self._components: Dict[UUID, Lifecycle] = {}
        self._dependencies: Dict[UUID, Set[UUID]] = defaultdict(set)
        self._handlers: Dict[ComponentState, Set[Callable[[UUID], None]]] = defaultdict(
            set
        )
        self._lock = asyncio.Lock()

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
                component = self._components[component_id]
                current_state = component.state
                self._validate_transition(component_id, current_state, target_state)
                component._state = target_state

                # Trigger state change handlers
                handlers = self._handlers[target_state]
                for handler in handlers:
                    try:
                        handler(component_id)
                    except Exception as e:
                        logger.error(
                            f"State change handler failed: {e}",
                            extra={
                                "component_id": str(component_id),
                                "state": target_state.name,
                                "error": str(e),
                            },
                        )

            except Exception as e:
                raise LifecycleError(
                    f"Failed to update state: {e}",
                    component=str(component_id),
                    state=target_state.name,
                )

    def register(self, component: Lifecycle) -> None:
        """Register a new component.

        Args:
            component: Component to register

        Raises:
            ValueError: If component is already registered
            LifecycleError: If registration fails

        """
        if component.id in self._components:
            raise ValueError(f"Component {component.id} already registered")

        try:
            self._components[component.id] = component
            component._state = ComponentState.REGISTERED
        except Exception as e:
            raise LifecycleError(
                f"Failed to register component: {e}",
                component=str(component.id),
            )

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
            )

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
            )

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
            )

    async def terminate(self, component_id: UUID) -> None:
        """Terminate a component.

        Args:
            component_id: Component identifier

        Raises:
            StateError: If component is in invalid state
            LifecycleError: If termination fails

        """
        try:
            component = self._components[component_id]
            await self._update_state(component_id, ComponentState.TERMINATED)
            await component.cleanup()
            del self._components[component_id]
            self._dependencies.pop(component_id, None)
        except Exception as e:
            await self._update_state(component_id, ComponentState.ERROR)
            raise LifecycleError(
                f"Failed to terminate component: {e}",
                component=str(component_id),
            )

    async def shutdown(self) -> None:
        """Shutdown all components in reverse dependency order."""
        # Get components in reverse dependency order
        components = list(self._components.keys())
        components.sort(key=lambda x: len(self._dependencies[x]), reverse=True)

        for component_id in components:
            try:
                await self.terminate(component_id)
            except Exception as e:
                logger.error(
                    f"Error shutting down {component_id}: {e}",
                    extra={"component_id": str(component_id)},
                )

    def add_dependency(self, component_id: UUID, dependency_id: UUID) -> None:
        """Add a dependency between components.

        Args:
            component_id: Component that depends on another
            dependency_id: Component being depended on

        Raises:
            ValueError: If either component is not registered
            LifecycleError: If dependency addition fails

        """
        if component_id not in self._components:
            raise ValueError(f"Component {component_id} not registered")
        if dependency_id not in self._components:
            raise ValueError(f"Dependency {dependency_id} not registered")

        self._dependencies[component_id].add(dependency_id)

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
            state: State being handled
            handler: Handler function to remove

        """
        self._handlers[state].discard(handler)

    def get_dependencies(self, component_id: UUID) -> Set[UUID]:
        """Get dependencies for a component.

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
            True if component is in RUNNING state

        """
        component = self._components.get(component_id)
        return component is not None and component.state == ComponentState.RUNNING
