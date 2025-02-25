"""Lifecycle manager module.

This module provides the lifecycle manager for managing component lifecycles.
"""

from __future__ import annotations

import asyncio
from typing import Any

from pepperpy.core.lifecycle.base import LifecycleComponent
from pepperpy.core.lifecycle.errors import (
    InvalidStateError,
    InvalidTransitionError,
    LifecycleOperationError,
)
from pepperpy.core.lifecycle.types import LifecycleState
from pepperpy.core.protocols.lifecycle import Lifecycle


class LifecycleManager(Lifecycle):
    """Manager for component lifecycles."""

    def __init__(self, name: str = "lifecycle") -> None:
        """Initialize lifecycle manager.

        Args:
            name: Manager name
        """
        self.name = name
        self._components: dict[str, LifecycleComponent] = {}

    async def initialize(self) -> None:
        """Initialize manager.

        Raises:
            LifecycleOperationError: If initialization fails
        """
        try:
            # Initialize components in parallel
            tasks = [component.initialize() for component in self._components.values()]
            await asyncio.gather(*tasks)
        except Exception as e:
            raise LifecycleOperationError(f"Failed to initialize components: {e}")

    async def cleanup(self) -> None:
        """Clean up manager.

        Raises:
            LifecycleOperationError: If cleanup fails
        """
        try:
            # Clean up components in parallel
            tasks = [component.cleanup() for component in self._components.values()]
            await asyncio.gather(*tasks)
        except Exception as e:
            raise LifecycleOperationError(f"Failed to clean up components: {e}")

    def register(self, component: LifecycleComponent) -> None:
        """Register a component.

        Args:
            component: Component to register

        Raises:
            ValueError: If component already registered
        """
        if component.name in self._components:
            raise ValueError(f"Component already registered: {component.name}")
        self._components[component.name] = component

    def unregister(self, name: str) -> None:
        """Unregister a component.

        Args:
            name: Component name

        Raises:
            ValueError: If component not found
        """
        if name not in self._components:
            raise ValueError(f"Component not found: {name}")
        del self._components[name]

    def get_component(self, name: str) -> LifecycleComponent:
        """Get a component by name.

        Args:
            name: Component name

        Returns:
            LifecycleComponent: Component instance

        Raises:
            ValueError: If component not found
        """
        if name not in self._components:
            raise ValueError(f"Component not found: {name}")
        return self._components[name]

    def list_components(self) -> list[LifecycleComponent]:
        """List all registered components.

        Returns:
            list[LifecycleComponent]: List of components
        """
        return list(self._components.values())

    def get_component_state(self, name: str) -> LifecycleState:
        """Get component state.

        Args:
            name: Component name

        Returns:
            LifecycleState: Component state

        Raises:
            ValueError: If component not found
        """
        component = self.get_component(name)
        return component.state

    def get_component_metadata(self, name: str) -> dict[str, Any]:
        """Get component metadata.

        Args:
            name: Component name

        Returns:
            dict[str, Any]: Component metadata

        Raises:
            ValueError: If component not found
        """
        component = self.get_component(name)
        return {
            "name": component.name,
            "state": component.state,
            "type": type(component).__name__,
        }

    def validate_state(self, name: str, state: LifecycleState) -> bool:
        """Validate component state.

        Args:
            name: Component name
            state: Expected state

        Returns:
            bool: True if state is valid

        Raises:
            ValueError: If component not found
            InvalidStateError: If state is invalid
        """
        component = self.get_component(name)
        if component.state != state:
            raise InvalidStateError(
                f"Invalid state for {name}: {component.state} != {state}"
            )
        return True

    def validate_transition(self, name: str, target_state: LifecycleState) -> bool:
        """Validate state transition.

        Args:
            name: Component name
            target_state: Target state

        Returns:
            bool: True if transition is valid

        Raises:
            ValueError: If component not found
            InvalidTransitionError: If transition is invalid
        """
        component = self.get_component(name)
        if not component.is_valid_transition(target_state):
            raise InvalidTransitionError(
                f"Invalid transition for {name}: {component.state} -> {target_state}"
            )
        return True


# Export public API
__all__ = [
    "LifecycleManager",
]
