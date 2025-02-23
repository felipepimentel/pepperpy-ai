"""Lifecycle manager module.

This module provides a manager for handling multiple lifecycle components.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Type

from pepperpy.lifecycle.base import BaseLifecycle
from pepperpy.lifecycle.errors import (
    StateError,
)
from pepperpy.lifecycle.types import (
    LifecycleConfig,
    LifecycleHook,
    LifecycleState,
)

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manager for handling multiple lifecycle components."""

    def __init__(self, config: Optional[LifecycleConfig] = None) -> None:
        """Initialize lifecycle manager.

        Args:
            config: Optional lifecycle configuration
        """
        self._config = config or LifecycleConfig()
        self._components: Dict[str, BaseLifecycle] = {}
        self._hooks: Set[LifecycleHook] = set()
        self._lock = asyncio.Lock()

    @property
    def config(self) -> LifecycleConfig:
        """Get lifecycle configuration."""
        return self._config

    def get_component(self, component_id: str) -> Optional[BaseLifecycle]:
        """Get component by ID.

        Args:
            component_id: Component ID

        Returns:
            Component instance or None if not found
        """
        return self._components.get(component_id)

    def get_components(self) -> List[BaseLifecycle]:
        """Get all components.

        Returns:
            List of component instances
        """
        return list(self._components.values())

    def get_components_by_state(self, state: LifecycleState) -> List[BaseLifecycle]:
        """Get components by state.

        Args:
            state: Lifecycle state

        Returns:
            List of component instances in the specified state
        """
        return [
            component
            for component in self._components.values()
            if component.get_state() == state
        ]

    def add_hook(self, hook: LifecycleHook) -> None:
        """Add lifecycle hook.

        Args:
            hook: Hook to add
        """
        self._hooks.add(hook)
        for component in self._components.values():
            component.add_hook(hook)

    def remove_hook(self, hook: LifecycleHook) -> None:
        """Remove lifecycle hook.

        Args:
            hook: Hook to remove
        """
        self._hooks.discard(hook)
        for component in self._components.values():
            component.remove_hook(hook)

    async def register_component(
        self,
        component_id: str,
        component_type: Type[BaseLifecycle],
        config: Optional[LifecycleConfig] = None,
    ) -> BaseLifecycle:
        """Register component.

        Args:
            component_id: Component ID
            component_type: Component type
            config: Optional lifecycle configuration

        Returns:
            Component instance

        Raises:
            StateError: If component already exists
        """
        async with self._lock:
            if component_id in self._components:
                raise StateError(
                    message=f"Component already exists: {component_id}",
                    component_id=component_id,
                    state=self._components[component_id].get_state(),
                )

            component = component_type(
                component_id=component_id,
                config=config or self._config,
            )

            # Add hooks
            for hook in self._hooks:
                component.add_hook(hook)

            self._components[component_id] = component
            return component

    async def unregister_component(self, component_id: str) -> None:
        """Unregister component.

        Args:
            component_id: Component ID

        Raises:
            StateError: If component not found
        """
        async with self._lock:
            if component_id not in self._components:
                raise StateError(
                    message=f"Component not found: {component_id}",
                    component_id=component_id,
                    state=LifecycleState.UNINITIALIZED,
                )

            component = self._components[component_id]
            if component.get_state() not in {
                LifecycleState.UNINITIALIZED,
                LifecycleState.FINALIZED,
                LifecycleState.ERROR,
            }:
                raise StateError(
                    message=f"Component must be uninitialized, finalized, or in error state: {component_id}",
                    component_id=component_id,
                    state=component.get_state(),
                )

            del self._components[component_id]

    async def initialize_component(self, component_id: str) -> None:
        """Initialize component.

        Args:
            component_id: Component ID

        Raises:
            StateError: If component not found
            InitializationError: If initialization fails
        """
        component = self.get_component(component_id)
        if not component:
            raise StateError(
                message=f"Component not found: {component_id}",
                component_id=component_id,
                state=LifecycleState.UNINITIALIZED,
            )

        await component.initialize()

    async def start_component(self, component_id: str) -> None:
        """Start component.

        Args:
            component_id: Component ID

        Raises:
            StateError: If component not found
            StartError: If start fails
        """
        component = self.get_component(component_id)
        if not component:
            raise StateError(
                message=f"Component not found: {component_id}",
                component_id=component_id,
                state=LifecycleState.UNINITIALIZED,
            )

        await component.start()

    async def stop_component(self, component_id: str) -> None:
        """Stop component.

        Args:
            component_id: Component ID

        Raises:
            StateError: If component not found
            StopError: If stop fails
        """
        component = self.get_component(component_id)
        if not component:
            raise StateError(
                message=f"Component not found: {component_id}",
                component_id=component_id,
                state=LifecycleState.UNINITIALIZED,
            )

        await component.stop()

    async def finalize_component(self, component_id: str) -> None:
        """Finalize component.

        Args:
            component_id: Component ID

        Raises:
            StateError: If component not found
            FinalizeError: If finalization fails
        """
        component = self.get_component(component_id)
        if not component:
            raise StateError(
                message=f"Component not found: {component_id}",
                component_id=component_id,
                state=LifecycleState.UNINITIALIZED,
            )

        await component.finalize()

    async def initialize_all(self) -> None:
        """Initialize all components.

        Raises:
            InitializationError: If initialization fails
        """
        components = self.get_components_by_state(LifecycleState.UNINITIALIZED)
        await asyncio.gather(
            *(component.initialize() for component in components),
            return_exceptions=True,
        )

    async def start_all(self) -> None:
        """Start all components.

        Raises:
            StartError: If start fails
        """
        components = self.get_components_by_state(LifecycleState.INITIALIZED)
        await asyncio.gather(
            *(component.start() for component in components),
            return_exceptions=True,
        )

    async def stop_all(self) -> None:
        """Stop all components.

        Raises:
            StopError: If stop fails
        """
        components = self.get_components_by_state(LifecycleState.RUNNING)
        await asyncio.gather(
            *(component.stop() for component in components),
            return_exceptions=True,
        )

    async def finalize_all(self) -> None:
        """Finalize all components.

        Raises:
            FinalizeError: If finalization fails
        """
        components = self.get_components_by_state(LifecycleState.STOPPED)
        await asyncio.gather(
            *(component.finalize() for component in components),
            return_exceptions=True,
        )
