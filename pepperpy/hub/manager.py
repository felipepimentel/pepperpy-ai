"""Hub management functionality for PepperPy.

This module provides centralized management of PepperPy's component hub.
"""

import logging
from typing import Any, Dict, Optional

from pepperpy.common.base import Lifecycle
from pepperpy.common.types import ComponentState

logger = logging.getLogger(__name__)


class HubManager(Lifecycle):
    """Manager for PepperPy's component hub."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize hub manager.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        self._components: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the hub system."""
        try:
            # Initialize core components
            self._initialize_core_components()

            # Load plugins if configured
            if self.config.get("load_plugins", True):
                await self._load_plugins()

            self._state = ComponentState.RUNNING
            logger.info("Hub system initialized")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to initialize hub: {e}")
            raise RuntimeError(f"Failed to initialize hub manager: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up the hub system."""
        try:
            # Cleanup all components
            for component_id, component in self._components.items():
                try:
                    if hasattr(component, "cleanup"):
                        await component.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup component {component_id}: {e}")

            self._components.clear()
            self._state = ComponentState.UNREGISTERED
            logger.info("Hub system cleaned up")
        except Exception as e:
            self._state = ComponentState.ERROR
            logger.error(f"Failed to cleanup hub: {e}")
            raise RuntimeError(f"Failed to cleanup hub manager: {str(e)}") from e

    def register_component(self, component_id: str, component: Any) -> None:
        """Register a component with the hub.

        Args:
            component_id: Unique identifier for the component
            component: The component instance to register
        """
        if component_id in self._components:
            raise ValueError(f"Component {component_id} is already registered")
        self._components[component_id] = component
        logger.debug(f"Registered component: {component_id}")

    def get_component(self, component_id: str) -> Optional[Any]:
        """Get a registered component by ID.

        Args:
            component_id: ID of the component to retrieve

        Returns:
            The component instance if found, None otherwise
        """
        return self._components.get(component_id)

    def _initialize_core_components(self) -> None:
        """Initialize core system components."""
        # This would initialize essential components that should always be present
        pass

    async def _load_plugins(self) -> None:
        """Load and initialize plugins."""
        # This would handle dynamic loading of plugins based on configuration
        pass
