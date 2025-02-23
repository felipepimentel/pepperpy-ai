"""Hub-specific error types."""

from typing import Any

from pepperpy.core.errors import PepperError


class HubError(PepperError):
    """Base error class for hub operations."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize hub error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = {"error_code": "HUB001", **(details or {})}
        super().__init__(
            message,
            details=error_details,
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
    """Error raised by marketplace operations."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize marketplace error.

        Args:
            message: Error message
            details: Optional error details
        """
        error_details = {"error_code": "HUB002", **(details or {})}
        super().__init__(
            message,
            details=error_details,
        )


class HubNotFoundError(HubError):
    """Error raised when a hub cannot be found."""

    pass
