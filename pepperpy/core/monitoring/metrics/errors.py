"""Error definitions for the metrics module."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class MetricsError(PepperpyError):
    """Raised when a metrics operation fails.

    This error is raised when there is a problem with metrics operations,
    such as recording, exporting, or configuration issues.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the metrics error."""
        super().__init__(
            message,
            "ERR010",
            details,
            user_message,
            recovery_hint,
        )
