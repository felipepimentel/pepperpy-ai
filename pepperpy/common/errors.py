"""Common error classes for the Pepperpy framework."""

from typing import Any


class PepperpyError(Exception):
    """Base class for all Pepperpy errors.

    Attributes:
        message: Error message
        details: Additional error details

    Example:
        >>> raise PepperpyError("Something went wrong", details={"code": 500})
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize the error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigError(PepperpyError):
    """Raised when configuration is invalid.

    Example:
        >>> raise ConfigError("Invalid configuration", details={"field": "api_key"})
    """


class ProviderError(PepperpyError):
    """Base class for provider-related errors.

    Attributes:
        message: Error message
        provider_type: Type of provider that raised the error
        details: Additional error details

    Example:
        >>> raise ProviderError(
        ...     "API error",
        ...     provider_type="openai",
        ...     details={"status": 500}
        ... )
    """

    def __init__(
        self, message: str, provider_type: str, details: dict[str, Any] | None = None
    ) -> None:
        """Initialize the error.

        Args:
            message: Error message
            provider_type: Type of provider that raised the error
            details: Additional error details
        """
        super().__init__(message, details)
        self.provider_type = provider_type


class ProviderConfigError(ProviderError):
    """Raised when provider configuration is invalid.

    Example:
        >>> raise ProviderConfigError(
        ...     "Invalid configuration",
        ...     provider_type="openai",
        ...     details={"field": "api_key"}
        ... )
    """
