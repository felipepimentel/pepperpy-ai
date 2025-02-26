"""Core context module.

This module provides context management functionality.
"""

from contextvars import ContextVar
from typing import Any

_context: ContextVar[dict[str, Any]] = ContextVar("context", default={})


def get_context() -> dict[str, Any]:
    """Get current context.

    Returns:
        Current context
    """
    return _context.get()


def set_context(context: dict[str, Any]) -> None:
    """Set current context.

    Args:
        context: New context
    """
    _context.set(context)


def update_context(key: str, value: Any) -> None:
    """Update context value.

    Args:
        key: Context key
        value: Context value
    """
    context = get_context()
    context[key] = value
    set_context(context)


def get_context_value(key: str, default: Any | None = None) -> Any:
    """Get context value.

    Args:
        key: Context key
        default: Default value

    Returns:
        Context value
    """
    return get_context().get(key, default)


def clear_context() -> None:
    """Clear current context."""
    set_context({})
