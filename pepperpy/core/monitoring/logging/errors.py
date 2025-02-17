"""Error definitions for the logging module."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class LoggingError(PepperpyError):
    """Raised when a logging operation fails.

    This error is raised when there is a problem with logging operations,
    such as configuration issues or handler failures.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the logging error."""
        super().__init__(
            message,
            "ERR009",
            details,
            user_message,
            recovery_hint,
        )
