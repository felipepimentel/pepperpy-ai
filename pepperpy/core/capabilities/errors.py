"""Error types for capability management."""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class CapabilityError(PepperpyError):
    """Base class for capability-related errors."""

    def __init__(
        self,
        message: str,
        capability_name: Optional[str] = None,
        capability_version: Optional[str] = None,
        error_code: str = "CAPABILITY_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            capability_name: Optional name of the capability that caused the error
            capability_version: Optional version of the capability
            error_code: Error code
            details: Optional additional error details

        """
        super().__init__(message, error_code=error_code, details=details)
        self.capability_name = capability_name
        self.capability_version = capability_version


class CapabilityNotFoundError(CapabilityError):
    """Raised when a requested capability is not found."""

    def __init__(
        self,
        capability_name: str,
        version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            capability_name: Name of the capability that was not found
            version: Optional specific version that was not found
            details: Optional additional error details

        """
        message = f"Capability '{capability_name}' not found"
        if version:
            message += f" (version {version})"
        super().__init__(
            message,
            capability_name=capability_name,
            capability_version=version,
            error_code="CAPABILITY_NOT_FOUND",
            details=details,
        )


class CapabilityConfigError(CapabilityError):
    """Raised when there is an error in capability configuration."""

    def __init__(
        self,
        message: str,
        capability_name: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            capability_name: Name of the capability with invalid configuration
            config_key: Optional specific configuration key that caused the error
            details: Optional additional error details

        """
        super().__init__(
            message,
            capability_name=capability_name,
            error_code="CAPABILITY_CONFIG_ERROR",
            details={"config_key": config_key, **(details or {})},
        )
        self.config_key = config_key


class CapabilityInitError(CapabilityError):
    """Raised when capability initialization fails."""

    def __init__(
        self,
        message: str,
        capability_name: str,
        version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            capability_name: Name of the capability that failed to initialize
            version: Optional version of the capability
            details: Optional additional error details

        """
        super().__init__(
            message,
            capability_name=capability_name,
            capability_version=version,
            error_code="CAPABILITY_INIT_ERROR",
            details=details,
        )


class CapabilityCleanupError(CapabilityError):
    """Raised when capability cleanup fails."""

    def __init__(
        self,
        message: str,
        capability_name: str,
        version: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            capability_name: Name of the capability that failed to clean up
            version: Optional version of the capability
            details: Optional additional error details

        """
        super().__init__(
            message,
            capability_name=capability_name,
            capability_version=version,
            error_code="CAPABILITY_CLEANUP_ERROR",
            details=details,
        )
