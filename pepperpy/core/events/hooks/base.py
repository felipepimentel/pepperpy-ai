"""Hooks system for the Pepperpy framework.

This module provides the hook system that allows extending and customizing
the framework's behavior through callbacks and event handlers.
"""

from typing import Any, Dict, Optional, Protocol, Set, TypeVar

from pepperpy.monitoring import logger

# Configure logging
logger = logger.getChild(__name__)

T = TypeVar("T")


class HookCallback(Protocol):
    """Protocol for hook callbacks."""

    def __call__(self, context: Any) -> None:
        """Execute the hook callback.

        Args:
            context: Context information for the hook execution.
        """
        ...


class HookManager:
    """Manages lifecycle hooks and event handlers."""

    def __init__(self) -> None:
        """Initialize the hook manager."""
        self._hooks: Dict[str, Set[HookCallback]] = {}

    def register(self, event: str, callback: HookCallback) -> None:
        """Register a hook callback for an event.

        Args:
            event: Event to hook into
            callback: Callback to execute when event occurs

        Raises:
            ValueError: If event or callback is invalid
        """
        if not event or not isinstance(event, str):
            raise ValueError("Event must be a non-empty string")
        if not callable(callback):
            raise ValueError("Callback must be callable")

        if event not in self._hooks:
            self._hooks[event] = set()
        self._hooks[event].add(callback)
        logger.debug(f"Registered hook for event: {event}")

    def unregister(self, event: str, callback: HookCallback) -> None:
        """Unregister a hook callback.

        Args:
            event: Event to remove hook from
            callback: Callback to remove

        Raises:
            ValueError: If event is invalid
        """
        if not event or not isinstance(event, str):
            raise ValueError("Event must be a non-empty string")

        if event in self._hooks:
            self._hooks[event].discard(callback)
            logger.debug(f"Unregistered hook for event: {event}")

    def trigger(self, event: str, context: Optional[Any] = None) -> None:
        """Trigger hooks for an event.

        Args:
            event: Event that occurred
            context: Optional context information

        Raises:
            ValueError: If event is invalid
        """
        if not event or not isinstance(event, str):
            raise ValueError("Event must be a non-empty string")

        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    callback(context)
                except Exception as e:
                    logger.error(f"Hook execution failed for event {event}: {e}")
                    # Continue executing other hooks

    def clear(self, event: Optional[str] = None) -> None:
        """Clear all hooks for an event or all events.

        Args:
            event: Optional event to clear hooks for. If None, clears all hooks.

        Raises:
            ValueError: If event is invalid
        """
        if event:
            if not isinstance(event, str):
                raise ValueError("Event must be a string")
            if event in self._hooks:
                self._hooks[event].clear()
                logger.debug(f"Cleared hooks for event: {event}")
        else:
            self._hooks.clear()
            logger.debug("Cleared all hooks")

    def get_hooks(self, event: str) -> Set[HookCallback]:
        """Get all hooks registered for an event.

        Args:
            event: Event to get hooks for

        Returns:
            Set of hook callbacks registered for the event

        Raises:
            ValueError: If event is invalid
        """
        if not event or not isinstance(event, str):
            raise ValueError("Event must be a non-empty string")

        return self._hooks.get(event, set())


# Global hook manager instance
hook_manager = HookManager()
