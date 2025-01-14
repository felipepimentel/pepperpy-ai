"""Provider exception classes."""

from collections.abc import Sequence
from typing import TypedDict


class ErrorContext(TypedDict):
    """Provider error context.

    Attributes:
        provider: Provider name
        operation: Operation name
        details: Additional error details
    """

    provider: str
    operation: str
    details: dict[str, str | int | float | bool | None]


class ProviderError(Exception):
    """Base exception for provider errors.

    This class provides detailed error information for provider operations.
    It includes context about the provider, operation, and error details.

    Attributes:
        message: Error message
        provider: Provider name
        operation: Operation that failed
        details: Additional error details
        cause: Original exception
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        operation: str = "",
        details: dict[str, str | int | float | bool | None] | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            provider: Provider name
            operation: Operation that failed
            details: Additional error details
            cause: Original exception
        """
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.operation = operation
        self.details = details or {}
        self.cause = cause


class ProviderNotFoundError(ProviderError):
    """Error raised when provider is not found.

    Attributes:
        provider: Provider name
        available_providers: List of available providers
    """

    def __init__(
        self,
        provider: str,
        available_providers: Sequence[str],
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            provider: Provider name
            available_providers: List of available providers
            details: Additional error details
        """
        message = (
            f"Provider not found: {provider}. "
            f"Available: {', '.join(available_providers)}"
        )
        super().__init__(
            message,
            provider=provider,
            operation="provider_lookup",
            details=details,
        )
        self.available_providers = available_providers


class ProviderConfigError(ProviderError):
    """Error raised when provider configuration is invalid.

    Attributes:
        message: Error message
        provider: Provider name
        config_path: Path to config file
        invalid_keys: List of invalid keys
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        config_path: str = "",
        invalid_keys: list[str] | None = None,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            provider: Provider name
            config_path: Path to config file
            invalid_keys: List of invalid keys
            details: Additional error details
        """
        super().__init__(
            message,
            provider=provider,
            operation="config_validation",
            details=details,
        )
        self.config_path = config_path
        self.invalid_keys = invalid_keys or []


class ProviderAPIError(ProviderError):
    """Error raised when provider API request fails.

    Attributes:
        message: Error message
        provider: Provider name
        status_code: HTTP status code
        response: API response data
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        status_code: int | None = None,
        response: dict[str, str | int | float | bool | None] | None = None,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            provider: Provider name
            status_code: HTTP status code
            response: API response data
            details: Additional error details
        """
        super().__init__(
            message,
            provider=provider,
            operation="api_request",
            details=details,
        )
        self.status_code = status_code
        self.response = response or {}


class ProviderRateLimitError(ProviderError):
    """Error raised when provider rate limit is exceeded.

    Attributes:
        message: Error message
        provider: Provider name
        retry_after: Seconds to wait before retrying
    """

    def __init__(
        self,
        provider: str,
        retry_after: int | None = None,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            provider: Provider name
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        super().__init__(
            f"Rate limit exceeded for provider: {provider}",
            provider=provider,
            operation="rate_limit",
            details=details,
        )
        self.retry_after = retry_after


class ProviderAuthError(ProviderError):
    """Error raised when provider authentication fails.

    Attributes:
        message: Error message
        provider: Provider name
    """

    def __init__(
        self,
        provider: str,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            provider: Provider name
            details: Additional error details
        """
        super().__init__(
            f"Authentication failed for provider: {provider}",
            provider=provider,
            operation="authentication",
            details=details,
        )


class ProviderTimeoutError(ProviderError):
    """Error raised when provider request times out.

    Attributes:
        message: Error message
        provider: Provider name
        timeout: Timeout duration in seconds
    """

    def __init__(
        self,
        provider: str,
        timeout: float,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            provider: Provider name
            timeout: Timeout duration in seconds
            details: Additional error details
        """
        super().__init__(
            f"Request timed out for provider: {provider} after {timeout}s",
            provider=provider,
            operation="timeout",
            details=details,
        )
        self.timeout = timeout


class ProviderValidationError(ProviderError):
    """Error raised when provider input validation fails.

    Attributes:
        message: Error message
        provider: Provider name
        field: Field that failed validation
        value: Invalid value
        constraints: Validation constraints
    """

    def __init__(
        self,
        message: str,
        provider: str,
        field: str = "",
        value: str | int | float | bool | None = None,
        constraints: dict[str, str | int | float | bool | None] | None = None,
        details: dict[str, str | int | float | bool | None] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            provider: Provider name
            field: Field that failed validation
            value: Invalid value
            constraints: Validation constraints
            details: Additional error details
        """
        super().__init__(
            message,
            provider=provider,
            operation="validation",
            details=details,
        )
        self.field = field
        self.value = value
        self.constraints = constraints or {}
