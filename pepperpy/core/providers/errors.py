"""Provider-specific error classes and exception handling.

This module defines error classes and exception handling specific to
provider operations. It includes:
- Base provider errors
- Configuration errors
- Runtime errors
- Resource errors
"""

from typing import Any, Dict, Optional

from pepperpy.core.errors import ConfigurationError


class ProviderError(Exception):
    """Base class for provider-related errors.

    Attributes:
        message: Error message
        provider_type: Provider type identifier
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        provider_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider error.

        Args:
            message: Error message
            provider_type: Optional provider type identifier
            details: Optional error details
        """
        super().__init__(message)
        self.provider_type = provider_type
        self.details = details or {}


class ProviderNotFoundError(ProviderError):
    """Error raised when provider is not found.

    This error is raised when attempting to use a provider that
    is not registered or available.
    """

    def __init__(
        self, provider_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize provider not found error.

        Args:
            provider_type: Provider type identifier
            details: Optional error details
        """
        super().__init__(
            f"Provider not found: {provider_type}",
            provider_type=provider_type,
            details=details,
        )


class ProviderConfigurationError(ConfigurationError):
    """Error raised when provider configuration is invalid.

    This error is raised when provider configuration is missing
    required fields or contains invalid values.
    """

    def __init__(
        self,
        message: str,
        provider_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider configuration error.

        Args:
            message: Error message
            provider_type: Optional provider type identifier
            details: Optional error details
        """
        super().__init__(message)
        self.provider_type = provider_type
        self.details = details or {}


class ProviderRuntimeError(ProviderError):
    """Error raised during provider runtime operations.

    This error is raised when a provider encounters an error
    during execution or operation.
    """

    def __init__(
        self,
        message: str,
        provider_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider runtime error.

        Args:
            message: Error message
            provider_type: Optional provider type identifier
            details: Optional error details
        """
        super().__init__(message, provider_type=provider_type, details=details)


class ProviderResourceError(ProviderError):
    """Error raised when provider resource operations fail.

    This error is raised when a provider fails to allocate,
    access, or clean up resources.
    """

    def __init__(
        self,
        message: str,
        provider_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize provider resource error.

        Args:
            message: Error message
            provider_type: Optional provider type identifier
            details: Optional error details
        """
        super().__init__(message, provider_type=provider_type, details=details)
