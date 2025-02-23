"""Lifecycle management for components.

This module provides lifecycle management functionality for components,
including initialization, cleanup, and state management.

Status: Stable
"""

from __future__ import annotations

import asyncio
import logging
from typing import TypeVar

from pepperpy.core.errors import LifecycleError
from pepperpy.core.types import ComponentState, Lifecycle

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")
T_Lifecycle = TypeVar("T_Lifecycle", bound="Lifecycle")


class LifecycleManager:
    """Manager for component lifecycles.

    This class manages the lifecycle of multiple components, ensuring they are
    initialized and cleaned up in the correct order.
    """

    def __init__(self) -> None:
        """Initialize lifecycle manager."""
        self._components: dict[str, Lifecycle] = {}
        self._states: dict[str, ComponentState] = {}
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(__name__)

    def register(self, name: str, component: Lifecycle) -> None:
        """Register a component.

        Args:
            name: Component name
            component: Component instance

        Raises:
            ValueError: If component is already registered
        """
        if name in self._components:
            raise ValueError(f"Component already registered: {name}")

        self._components[name] = component
        self._states[name] = ComponentState.CREATED

    def unregister(self, name: str) -> None:
        """Unregister a component.

        Args:
            name: Component name

        Raises:
            ValueError: If component is not registered
        """
        if name not in self._components:
            raise ValueError(f"Component not registered: {name}")

        del self._components[name]
        del self._states[name]

    async def initialize(self, name: str) -> None:
        """Initialize a component.

        Args:
            name: Component name

        Raises:
            ValueError: If component is not registered
            LifecycleError: If initialization fails
        """
        if name not in self._components:
            raise ValueError(f"Component not registered: {name}")

        async with self._lock:
            state = self._states[name]
            if state != ComponentState.CREATED:
                raise LifecycleError(f"Cannot initialize component in state: {state}")

            try:
                self._states[name] = ComponentState.INITIALIZING
                await self._components[name].initialize()
                self._states[name] = ComponentState.READY
            except Exception as e:
                self._states[name] = ComponentState.ERROR
                raise LifecycleError(f"Failed to initialize component: {name}") from e

    async def cleanup(self, name: str) -> None:
        """Clean up a component.

        Args:
            name: Component name

        Raises:
            ValueError: If component is not registered
            LifecycleError: If cleanup fails
        """
        if name not in self._components:
            raise ValueError(f"Component not registered: {name}")

        async with self._lock:
            state = self._states[name]
            if state not in (ComponentState.READY, ComponentState.ERROR):
                raise LifecycleError(f"Cannot cleanup component in state: {state}")

            try:
                self._states[name] = ComponentState.CLEANING
                await self._components[name].cleanup()
                self._states[name] = ComponentState.CLEANED
            except Exception as e:
                self._states[name] = ComponentState.ERROR
                raise LifecycleError(f"Failed to cleanup component: {name}") from e

    async def initialize_all(self) -> None:
        """Initialize all components.

        Raises:
            LifecycleError: If initialization fails
        """
        for name in self._components:
            await self.initialize(name)

    async def cleanup_all(self) -> None:
        """Clean up all components.

        Raises:
            LifecycleError: If cleanup fails
        """
        for name in reversed(list(self._components)):
            await self.cleanup(name)

    def get_state(self, name: str) -> ComponentState:
        """Get component state.

        Args:
            name: Component name

        Returns:
            Component state

        Raises:
            ValueError: If component is not registered
        """
        if name not in self._components:
            raise ValueError(f"Component not registered: {name}")

        return self._states[name]

    def get_components(self) -> dict[str, Lifecycle]:
        """Get all registered components.

        Returns:
            Dictionary of component names to instances
        """
        return self._components.copy()

    def get_states(self) -> dict[str, ComponentState]:
        """Get all component states.

        Returns:
            Dictionary of component names to states
        """
        return self._states.copy()
