"""
Component termination management for Pepperpy.
"""
from typing import Any, Callable, Dict, List, Optional

from pepperpy.core.utils.errors import PepperpyError


class TerminationError(PepperpyError):
    """Error raised during component termination."""
    pass


class Terminator:
    """Manages component termination in the Pepperpy system."""

    def __init__(self) -> None:
        """Initialize the Terminator."""
        self._cleanup_handlers: Dict[str, List[Callable[[], None]]] = {}
        self._terminated_components: List[str] = []

    def register_cleanup(self, component_id: str, cleanup_handler: Callable[[], None]) -> None:
        """Register a cleanup handler for a component.

        Args:
            component_id: Unique identifier for the component.
            cleanup_handler: Function to call during cleanup.

        Raises:
            TerminationError: If registration fails.
        """
        try:
            if component_id not in self._cleanup_handlers:
                self._cleanup_handlers[component_id] = []
            self._cleanup_handlers[component_id].append(cleanup_handler)
        except Exception as e:
            raise TerminationError(
                f"Failed to register cleanup handler for component {component_id}: {str(e)}"
            ) from e

    def terminate_component(self, component_id: str, force: bool = False) -> None:
        """Terminate a component and run its cleanup handlers.

        Args:
            component_id: Unique identifier for the component.
            force: Whether to continue on cleanup errors.

        Raises:
            TerminationError: If termination fails and force is False.
        """
        if component_id in self._terminated_components:
            return

        handlers = self._cleanup_handlers.get(component_id, [])
        errors: List[Exception] = []

        for handler in handlers:
            try:
                handler()
            except Exception as e:
                errors.append(e)
                if not force:
                    raise TerminationError(
                        f"Failed to terminate component {component_id}: {str(e)}"
                    ) from e

        if not errors:
            self._terminated_components.append(component_id)
            self._cleanup_handlers.pop(component_id, None)
        elif force:
            # Log errors but continue if force is True
            error_messages = "; ".join(str(e) for e in errors)
            print(f"Forced termination of {component_id} with errors: {error_messages}")

    def terminate_all(self, force: bool = False) -> None:
        """Terminate all registered components.

        Args:
            force: Whether to continue on cleanup errors.

        Raises:
            TerminationError: If any termination fails and force is False.
        """
        components = list(self._cleanup_handlers.keys())
        errors: List[Exception] = []

        for component_id in components:
            try:
                self.terminate_component(component_id, force=force)
            except Exception as e:
                errors.append(e)
                if not force:
                    raise TerminationError(
                        f"Failed to terminate components: {str(e)}"
                    ) from e

        if errors and force:
            # Log errors but continue if force is True
            error_messages = "; ".join(str(e) for e in errors)
            print(f"Forced termination completed with errors: {error_messages}")

    def is_terminated(self, component_id: str) -> bool:
        """Check if a component has been terminated.

        Args:
            component_id: Unique identifier for the component.

        Returns:
            True if the component has been terminated.
        """
        return component_id in self._terminated_components

    def reset(self) -> None:
        """Reset the terminator state."""
        self._cleanup_handlers.clear()
        self._terminated_components.clear() 