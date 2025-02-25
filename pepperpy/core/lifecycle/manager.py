"""Lifecycle manager module.

This module provides the lifecycle manager for managing component lifecycles.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from pepperpy.core.errors import LifecycleError, NotFoundError
from pepperpy.core.lifecycle.types import Lifecycle, LifecycleState


class LifecycleManager:
    """Manager for component lifecycles."""

    def __init__(self) -> None:
        """Initialize lifecycle manager."""
        self._components: dict[str, Lifecycle] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, component: Lifecycle) -> None:
        """Register component.

        Args:
            component: Component to register

        Raises:
            LifecycleError: If component already registered
        """
        if component.name in self._components:
            raise LifecycleError(
                f"Component already registered: {component.name}",
                recovery_hint="Use a unique name for each component.",
            )

        self._components[component.name] = component
        self.logger.debug(f"Registered component: {component.name}")

    def unregister(self, name: str) -> None:
        """Unregister component.

        Args:
            name: Component name

        Raises:
            NotFoundError: If component not found
        """
        if name not in self._components:
            raise NotFoundError(
                f"Component not found: {name}",
                recovery_hint="Check if the component was registered.",
            )

        del self._components[name]
        self.logger.debug(f"Unregistered component: {name}")

    def get_component(self, name: str) -> Lifecycle:
        """Get component.

        Args:
            name: Component name

        Returns:
            Lifecycle: Component instance

        Raises:
            NotFoundError: If component not found
        """
        if name not in self._components:
            raise NotFoundError(
                f"Component not found: {name}",
                recovery_hint="Check if the component was registered.",
            )

        return self._components[name]

    async def initialize_all(self) -> None:
        """Initialize all components.

        Raises:
            LifecycleError: If initialization fails
        """
        try:
            self.logger.debug("Initializing all components")
            await asyncio.gather(
                *(component.initialize() for component in self._components.values())
            )
            self.logger.debug("Initialized all components")
        except Exception as e:
            raise LifecycleError(
                "Failed to initialize components",
                recovery_hint="Check component initialization logs for details.",
            ) from e

    async def cleanup_all(self) -> None:
        """Clean up all components.

        Raises:
            LifecycleError: If cleanup fails
        """
        try:
            self.logger.debug("Cleaning up all components")
            await asyncio.gather(
                *(component.cleanup() for component in self._components.values())
            )
            self.logger.debug("Cleaned up all components")
        except Exception as e:
            raise LifecycleError(
                "Failed to clean up components",
                recovery_hint="Check component cleanup logs for details.",
            ) from e

    async def list_components(
        self,
        state: LifecycleState | None = None,
    ) -> AsyncIterator[tuple[str, Any]]:
        """List components.

        Args:
            state: Optional state filter

        Yields:
            tuple[str, Any]: Component name and metadata
        """
        for name, component in self._components.items():
            if state and component._state != state:
                continue
            yield (
                name,
                {
                    "state": component._state,
                    "type": type(component).__name__,
                },
            )


__all__ = ["LifecycleManager"]
