"""Hub-specific error classes.

This module provides error classes specific to Hub operations.
"""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class HubError(PepperpyError):
    """Base class for Hub-related errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recovery_hint: Optional[str] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Technical error message.
            details: Optional dictionary of additional error details.
            user_message: Optional user-friendly error message.
            recovery_hint: Optional hint for recovering from the error.
        """
        super().__init__(
            message,
            details=details,
            user_message=user_message,
            recovery_hint=recovery_hint,
        )


class HubPublishingError(HubError):
    """Error raised during artifact publishing."""

    pass


class HubValidationError(HubError):
    """Error raised during artifact validation."""

    pass


class HubSecurityError(HubError):
    """Error raised during security operations."""

    pass


class HubStorageError(HubError):
    """Error raised during storage operations."""

    pass


class HubMarketplaceError(HubError):
    """Error raised during marketplace operations."""

    pass


class HubNotFoundError(HubError):
    """Error raised when a hub cannot be found."""

    pass
