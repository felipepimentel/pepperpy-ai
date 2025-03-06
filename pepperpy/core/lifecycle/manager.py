"""Lifecycle manager module.

This module provides the lifecycle manager implementation for coordinating
multiple lifecycle components.
"""

from collections import defaultdict
from typing import Any

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.errors import (
    FinalizeError,
    InitializationError,
    RetryError,
    StartError,
    StopError,
)
from pepperpy.core.lifecycle.hooks import LoggingHook, MetricsHook
from pepperpy.core.lifecycle.types import (
    LifecycleConfig,
    LifecycleContext,
    LifecycleEvent,
    LifecycleHook,
    LifecycleState,
)


class LifecycleManager:
    """Manager for coordinating multiple lifecycle components.

    This class provides functionality for managing multiple components
    with lifecycle support, including:
    - Component registration and dependency management
    - Coordinated initialization and startup
    - Graceful shutdown and cleanup
    - Metrics collection and monitoring
    """

    def __init__(
        self,
        config: LifecycleConfig | None = None,
        context: LifecycleContext | None = None,
    ) -> None:
        """Initialize the lifecycle manager.

        Args:
            config: Optional configuration for the manager
            context: Optional runtime context for the manager

        """
        self.config = config or LifecycleConfig()
        self.context = context or LifecycleContext(
            component_id="lifecycle_manager",
            state=LifecycleState.UNINITIALIZED,
            event=LifecycleEvent.INITIALIZE,
        )
        self.components: dict[str, LifecycleComponent] = {}
        self.dependencies: dict[str, set[str]] = defaultdict(set)
        self.hooks: list[LifecycleHook] = [LoggingHook(), MetricsHook()]

    def register_component(
        self,
        component: LifecycleComponent,
        dependencies: list[str] | None = None,
    ) -> None:
        """Register a component with the manager.

        Args:
            component: Component to register
            dependencies: Optional list of component IDs this component depends on

        """
        component_id = component.__class__.__name__
        self.components[component_id] = component
        if dependencies:
            self.dependencies[component_id].update(dependencies)

        # Add manager hooks to component
        for hook in self.hooks:
            component.add_hook(hook)

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add a lifecycle hook to all components.

        Args:
            hook: Hook to add

        """
        self.hooks.append(hook)
        for component in self.components.values():
            component.add_hook(hook)

    async def _initialize_component(self, component_id: str) -> None:
        """Initialize a component and its dependencies.

        Args:
            component_id: ID of component to initialize

        Raises:
            InitializationError: If initialization fails

        """
        # Initialize dependencies first
        for dep_id in self.dependencies[component_id]:
            if dep_id not in self.components:
                raise InitializationError(f"Missing dependency: {dep_id}")
            if self.components[dep_id].state == LifecycleState.UNINITIALIZED:
                await self._initialize_component(dep_id)

        # Initialize component
        try:
            await self.components[component_id].initialize()
        except Exception as e:
            raise InitializationError(
                f"Failed to initialize {component_id}: {e}",
            ) from e

    async def initialize(self) -> None:
        """Initialize all components.

        This method initializes all registered components in dependency order.

        Raises:
            InitializationError: If initialization fails

        """
        try:
            # Initialize all components that haven't been initialized
            for component_id in self.components:
                if self.components[component_id].state == LifecycleState.UNINITIALIZED:
                    await self._initialize_component(component_id)
        except Exception as e:
            raise InitializationError(f"Failed to initialize components: {e}") from e

    async def start(self) -> None:
        """Start all components.

        This method starts all initialized components in dependency order.

        Raises:
            StartError: If starting fails

        """
        try:
            # Start components in dependency order
            for component_id in self.components:
                component = self.components[component_id]
                if component.state == LifecycleState.READY:
                    await component.start()
        except Exception as e:
            raise StartError(f"Failed to start components: {e}") from e

    async def stop(self) -> None:
        """Stop all components.

        This method stops all running components in reverse dependency order.

        Raises:
            StopError: If stopping fails

        """
        try:
            # Stop components in reverse dependency order
            for component_id in reversed(list(self.components)):
                component = self.components[component_id]
                if component.state == LifecycleState.RUNNING:
                    await component.stop()
        except Exception as e:
            raise StopError(f"Failed to stop components: {e}") from e

    async def cleanup(self) -> None:
        """Clean up all components.

        This method cleans up all stopped components in reverse dependency order.

        Raises:
            FinalizeError: If cleanup fails

        """
        try:
            # Clean up components in reverse dependency order
            for component_id in reversed(list(self.components)):
                component = self.components[component_id]
                if component.state == LifecycleState.STOPPED:
                    await component.cleanup()
        except Exception as e:
            raise FinalizeError(f"Failed to clean up components: {e}") from e

    async def retry(self, operation: str, **kwargs: Any) -> None:
        """Retry a failed operation.

        Args:
            operation: Name of operation to retry
            **kwargs: Additional arguments for the operation

        Raises:
            RetryError: If retry fails

        """
        try:
            if operation == "initialize":
                await self.initialize()
            elif operation == "start":
                await self.start()
            elif operation == "stop":
                await self.stop()
            elif operation == "cleanup":
                await self.cleanup()
            else:
                raise ValueError(f"Unknown operation: {operation}")
        except Exception as e:
            raise RetryError(f"Failed to retry {operation}: {e}") from e
