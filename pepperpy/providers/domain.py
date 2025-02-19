"""Domain module for providers.

This module defines domain-specific classes and errors for providers.
"""

from typing import Any, Dict, Optional

from pepperpy.core.errors import PepperpyError


class ProviderError(PepperpyError):
    """Base class for provider errors."""

    def __init__(
        self,
        message: str,
        provider_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            message: Error message
            provider_type: Type of provider that raised the error
            details: Additional error details
        """
        super().__init__(message)
        self.provider_type = provider_type
        self.details = details or {}


class ProviderNotFoundError(ProviderError):
    """Error raised when a provider is not found."""

    def __init__(
        self,
        provider_type: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the error.

        Args:
        ----
            provider_type: Type of provider that was not found
            details: Additional error details
        """
        super().__init__(
            f"Provider not found: {provider_type}",
            provider_type=provider_type,
            details=details,
        )
