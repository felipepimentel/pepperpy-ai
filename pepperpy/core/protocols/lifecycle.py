"""Protocol for components with lifecycle management."""

from abc import abstractmethod
from typing import Protocol

from pepperpy.core.lifecycle.types import LifecycleState


class Lifecycle(Protocol):
    """Protocol defining lifecycle management for components.

    This protocol defines the standard interface for components that need
    lifecycle management (initialization, cleanup, state tracking).

    All components implementing this protocol must:
    1. Track their current state
    2. Support initialization
    3. Support cleanup
    4. Validate state transitions
    """

    @property
    @abstractmethod
    def state(self) -> LifecycleState:
        """Get the current lifecycle state.

        Returns:
            LifecycleState: Current state of the component
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the component.

        This method should:
        1. Set up any required resources
        2. Initialize internal state
        3. Validate configuration
        4. Connect to external services if needed

        Raises:
            LifecycleError: If initialization fails
            ConfigError: If configuration is invalid
            ResourceError: If required resources are unavailable
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up component resources.

        This method should:
        1. Release any acquired resources
        2. Close connections
        3. Cancel running tasks
        4. Reset internal state

        Raises:
            LifecycleError: If cleanup fails
            ResourceError: If resource cleanup fails
        """
        ...
