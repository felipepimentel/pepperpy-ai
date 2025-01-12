"""Provider exceptions module."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..exceptions import PepperPyAIError
from ..types import JsonDict


@dataclass
class ProviderErrorContext:
    """Provider error context.
    
    Attributes:
        provider: Provider name
        operation: Operation that failed
        request_id: Request identifier
        timestamp: Error timestamp
        details: Additional error details
    """
    provider: str = ""
    operation: str = ""
    request_id: str = field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = field(default_factory=datetime.now)
    details: JsonDict = field(default_factory=lambda: {})


class ProviderError(PepperPyAIError):
    """Base exception for provider errors.
    
    This class provides detailed error information for provider operations.
    It includes context about the provider, operation, and error details.
    """

    def __init__(
        self,
        message: str,
        provider: str = "",
        operation: str = "",
        cause: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message
            provider: Provider name
            operation: Operation that failed
            cause: Original exception
            **kwargs: Additional error details
        """
        super().__init__(message)
        self.provider = provider
        self.operation = operation
        self.cause = cause
        self.details = kwargs

class ProviderNotFoundError(ProviderError):
    """Error when provider is not found."""

    def __init__(
        self,
        provider: str,
        available_providers: list[str],
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            provider: Provider name
            available_providers: List of available providers
            **kwargs: Additional error details
        """
        super().__init__(
            f"Provider not found: {provider}. Available: {', '.join(available_providers)}",
            provider=provider,
            operation="provider_lookup",
            available_providers=available_providers,
            **kwargs
        )

class ProviderConfigError(ProviderError):
    """Error in provider configuration."""

    def __init__(
        self,
        message: str,
        provider: str,
        config_path: str = "",
        invalid_keys: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message
            provider: Provider name
            config_path: Path to config file
            invalid_keys: List of invalid configuration keys
            **kwargs: Additional error details
        """
        super().__init__(
            message,
            provider=provider,
            operation="configuration",
            config_path=config_path,
            invalid_keys=invalid_keys or [],
            **kwargs
        )

class ProviderAPIError(ProviderError):
    """Error in provider API call."""

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message
            provider: Provider name
            status_code: HTTP status code
            response: API response
            **kwargs: Additional error details
        """
        super().__init__(
            message,
            provider=provider,
            operation="api_call",
            status_code=status_code,
            response=response or {},
            **kwargs
        )

class ProviderRateLimitError(ProviderAPIError):
    """Error when provider rate limit is exceeded."""

    def __init__(
        self,
        provider: str,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            provider: Provider name
            retry_after: Seconds to wait before retry
            **kwargs: Additional error details
        """
        super().__init__(
            f"Rate limit exceeded for provider: {provider}",
            provider=provider,
            status_code=429,
            retry_after=retry_after,
            **kwargs
        )

class ProviderAuthError(ProviderAPIError):
    """Error in provider authentication."""

    def __init__(
        self,
        provider: str,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            provider: Provider name
            **kwargs: Additional error details
        """
        super().__init__(
            f"Authentication failed for provider: {provider}",
            provider=provider,
            status_code=401,
            **kwargs
        )

class ProviderTimeoutError(ProviderAPIError):
    """Error when provider request times out."""

    def __init__(
        self,
        provider: str,
        timeout: float,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            provider: Provider name
            timeout: Request timeout in seconds
            **kwargs: Additional error details
        """
        super().__init__(
            f"Request timed out for provider: {provider} (timeout: {timeout}s)",
            provider=provider,
            status_code=408,
            timeout=timeout,
            **kwargs
        )

class ProviderValidationError(ProviderError):
    """Error in provider input validation."""

    def __init__(
        self,
        message: str,
        provider: str,
        field: str = "",
        value: Any = None,
        constraints: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize error.
        
        Args:
            message: Error message
            provider: Provider name
            field: Invalid field
            value: Invalid value
            constraints: Validation constraints
            **kwargs: Additional error details
        """
        super().__init__(
            message,
            provider=provider,
            operation="validation",
            field=field,
            value=value,
            constraints=constraints or {},
            **kwargs
        )
