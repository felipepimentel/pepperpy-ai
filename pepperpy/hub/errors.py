"""Hub-specific error types."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class HubError(PepperpyError):
    """Base class for hub-related errors."""

    def __init__(
        self,
        message: str,
        hub: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize hub error.

        Args:
            message: Error message
            hub: Name of the hub
            details: Additional error details

        """
        super().__init__(
            message,
            error_code="HUB_ERROR",
            details={
                "hub": hub,
                **(details or {}),
            },
        )


class HubNotFoundError(HubError):
    """Error raised when a hub is not found."""

    def __init__(self, hub: str) -> None:
        """Initialize hub not found error.

        Args:
            hub: Name of the hub that was not found

        """
        super().__init__(
            f"Hub {hub} not found",
            hub=hub,
            details={"error_code": "HUB_NOT_FOUND"},
        )


class HubValidationError(HubError):
    """Error raised when hub validation fails."""

    def __init__(
        self,
        message: str,
        hub: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize hub validation error.

        Args:
            message: Error message
            hub: Name of the hub
            details: Additional error details

        """
        super().__init__(
            message,
            hub=hub,
            details={
                "error_code": "HUB_VALIDATION_ERROR",
                **(details or {}),
            },
        )


class ResourceError(HubError):
    """Error raised when resource operation fails."""

    def __init__(
        self,
        message: str,
        hub: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize resource error.

        Args:
            message: Error message
            hub: Name of the hub
            resource: Resource identifier
            details: Additional error details

        """
        super().__init__(
            message,
            hub=hub,
            details={
                "error_code": "RESOURCE_ERROR",
                "resource": resource,
                **(details or {}),
            },
        )


class ResourceNotFoundError(ResourceError):
    """Error raised when a resource is not found."""

    def __init__(
        self,
        hub: str,
        resource: str,
    ) -> None:
        """Initialize resource not found error.

        Args:
            hub: Name of the hub
            resource: Resource identifier that was not found

        """
        super().__init__(
            f"Resource {resource} not found in hub {hub}",
            hub=hub,
            resource=resource,
            details={"error_code": "RESOURCE_NOT_FOUND"},
        )
