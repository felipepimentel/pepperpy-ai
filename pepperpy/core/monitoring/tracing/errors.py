"""Error definitions for the tracing module."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class TracingError(PepperpyError):
    """Raised when a tracing operation fails.

    This error is raised when there is a problem with tracing operations,
    such as span creation, context propagation, or exporter failures.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the tracing error."""
        super().__init__(
            message,
            "ERR011",
            details,
            user_message,
            recovery_hint,
        )


class SpanError(TracingError):
    """Raised when a span operation fails."""

    pass


class ContextError(TracingError):
    """Raised when a context operation fails."""

    pass


class ExporterError(TracingError):
    """Raised when a tracing exporter operation fails."""

    pass
