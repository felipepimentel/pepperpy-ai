"""
Component state management for Pepperpy.
"""
from typing import Any, Dict, Optional

from pepperpy.core.utils.errors import PepperpyError


class StateError(PepperpyError):
    """Error raised during state management operations."""
    pass


class StateManager:
    """Manages component states in the Pepperpy system."""

    def __init__(self) -> None:
        """Initialize the StateManager."""
        self._states: Dict[str, Dict[str, Any]] = {}

    def set_state(self, component_id: str, state: Dict[str, Any]) -> None:
        """Set the state for a component.

        Args:
            component_id: Unique identifier for the component.
            state: State data to store.

        Raises:
            StateError: If state operation fails.
        """
        try:
            self._states[component_id] = state.copy()
        except Exception as e:
            raise StateError(f"Failed to set state for component {component_id}: {str(e)}") from e

    def get_state(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of a component.

        Args:
            component_id: Unique identifier for the component.

        Returns:
            The component's state or None if not found.

        Raises:
            StateError: If state retrieval fails.
        """
        try:
            return self._states.get(component_id, {}).copy()
        except Exception as e:
            raise StateError(f"Failed to get state for component {component_id}: {str(e)}") from e

    def update_state(self, component_id: str, updates: Dict[str, Any]) -> None:
        """Update part of a component's state.

        Args:
            component_id: Unique identifier for the component.
            updates: State updates to apply.

        Raises:
            StateError: If state update fails.
        """
        try:
            current_state = self._states.get(component_id, {})
            current_state.update(updates)
            self._states[component_id] = current_state
        except Exception as e:
            raise StateError(f"Failed to update state for component {component_id}: {str(e)}") from e

    def remove_state(self, component_id: str) -> None:
        """Remove a component's state.

        Args:
            component_id: Unique identifier for the component.

        Raises:
            StateError: If state removal fails.
        """
        try:
            self._states.pop(component_id, None)
        except Exception as e:
            raise StateError(f"Failed to remove state for component {component_id}: {str(e)}") from e

    def clear_all_states(self) -> None:
        """Clear all component states.

        Raises:
            StateError: If clearing states fails.
        """
        try:
            self._states.clear()
        except Exception as e:
            raise StateError(f"Failed to clear all states: {str(e)}") from e 