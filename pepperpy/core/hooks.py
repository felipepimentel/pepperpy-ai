"""Hooks system for the Pepperpy framework.

This module provides the hook system that allows extending and customizing
the framework's behavior through callbacks and event handlers.
"""

from typing import Any, Dict, Optional, Protocol, TypeVar

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
        self._hooks: Dict[str, set[HookCallback]] = {}

    def register(self, event: str, callback: HookCallback) -> None:
        """Register a hook callback for an event.

        Args:
            event: Event to hook into
            callback: Callback to execute when event occurs

        """
        if event not in self._hooks:
            self._hooks[event] = set()
        self._hooks[event].add(callback)

    def unregister(self, event: str, callback: HookCallback) -> None:
        """Unregister a hook callback.

        Args:
            event: Event to remove hook from
            callback: Callback to remove

        """
        if event in self._hooks:
            self._hooks[event].discard(callback)

    def trigger(self, event: str, context: Optional[Any] = None) -> None:
        """Trigger hooks for an event.

        Args:
            event: Event that occurred
            context: Optional context information

        """
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    callback(context)
                except Exception as e:
                    # Log error but continue executing other hooks
                    print(f"Hook execution failed: {e}")


# Global hook manager instance
hook_manager = HookManager()
