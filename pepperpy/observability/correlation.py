"""Correlation management for observability.

This module provides tools for correlating events and traces.
"""

import contextvars
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class CorrelationContext:
    """Context for correlated events."""

    def __init__(self, correlation_id: str | None = None, **context: Any) -> None:
        """Initialize correlation context.

        Args:
            correlation_id: Optional correlation ID
            **context: Additional context values
        """
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.context = context


# Global context variable
_correlation_context: contextvars.ContextVar[CorrelationContext | None] = (
    contextvars.ContextVar("correlation_context", default=None)
)


class CorrelationManager:
    """Manages correlation context."""

    def get_current_context(self) -> CorrelationContext | None:
        """Get current correlation context.

        Returns:
            Current correlation context or None
        """
        return _correlation_context.get()

    def set_context(
        self, context: CorrelationContext
    ) -> contextvars.Token[CorrelationContext | None]:
        """Set correlation context.

        Args:
            context: Context to set

        Returns:
            Token for resetting context
        """
        return _correlation_context.set(context)

    def reset_context(
        self, token: contextvars.Token[CorrelationContext | None]
    ) -> None:
        """Reset correlation context.

        Args:
            token: Token from set_context
        """
        _correlation_context.reset(token)

    @contextmanager
    def context(
        self, correlation_id: str | None = None, **context: Any
    ) -> Generator[CorrelationContext, None, None]:
        """Create a new correlation context.

        Args:
            correlation_id: Optional correlation ID
            **context: Additional context values

        Yields:
            New correlation context
        """
        ctx = CorrelationContext(correlation_id, **context)
        token = self.set_context(ctx)
        try:
            yield ctx
        finally:
            self.reset_context(token)

    def get_correlation_id(self) -> str | None:
        """Get current correlation ID.

        Returns:
            Current correlation ID or None
        """
        ctx = self.get_current_context()
        return ctx.correlation_id if ctx else None

    def get_context_value(self, key: str) -> Any | None:
        """Get value from current context.

        Args:
            key: Context key

        Returns:
            Context value or None
        """
        ctx = self.get_current_context()
        return ctx.context.get(key) if ctx else None

    def update_context(self, **context: Any) -> None:
        """Update current context.

        Args:
            **context: Context values to update
        """
        ctx = self.get_current_context()
        if ctx:
            ctx.context.update(context)


__all__ = ["CorrelationContext", "CorrelationManager"]
