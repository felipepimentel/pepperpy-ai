"""Unified error handling for PepperPy.

This module provides a centralized error class hierarchy for the entire
framework, with consistent error reporting, context, and handling mechanisms.
"""

from typing import Any, Dict, List, Optional, Type


class PepperpyError(Exception):
    """Base exception for all PepperPy errors.

    All errors in PepperPy should inherit from this class to ensure consistent
    error handling and reporting.
    """

    def __init__(
        self,
        message: str,
        *args,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        **kwargs,
    ):
        """Initialize a PepperPy error.

        Args:
            message: Error message
            *args: Additional positional arguments
            code: Optional error code
            details: Optional additional details
            cause: Optional exception that caused this error
            **kwargs: Additional named context values
        """
        super().__init__(message, *args)
        self.message = message
        self.code = code
        self.details = details or {}
        self.cause = cause

        # Store any additional context
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            String representation
        """
        parts = [self.message]

        if self.code:
            parts.insert(0, f"[{self.code}]")

        # Add all custom attributes
        for attr, value in self.__dict__.items():
            if attr not in (
                "message",
                "code",
                "details",
                "cause",
                "args",
            ) and not attr.startswith("_"):
                parts.append(f"{attr}={value}")

        # Add cause if available
        if self.cause:
            parts.append(f"caused by: {self.cause}")

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary.

        Returns:
            Dictionary representation of the error
        """
        result = {"type": self.__class__.__name__, "message": self.message}

        if self.code:
            result["code"] = self.code

        if self.details:
            result["details"] = self.details

        # Add all custom attributes
        for attr, value in self.__dict__.items():
            if attr not in (
                "message",
                "code",
                "details",
                "cause",
                "args",
            ) and not attr.startswith("_"):
                result[attr] = value

        # Add cause if available
        if self.cause:
            if isinstance(self.cause, PepperpyError):
                result["cause"] = self.cause.to_dict()
            else:
                result["cause"] = {
                    "type": self.cause.__class__.__name__,
                    "message": str(self.cause),
                }

        return result

    @classmethod
    def from_exception(
        cls, exception: Exception, message: Optional[str] = None, **kwargs
    ) -> "PepperpyError":
        """Create a PepperPy error from another exception.

        Args:
            exception: Original exception
            message: Optional custom message
            **kwargs: Additional context values

        Returns:
            PepperPy error
        """
        if isinstance(exception, cls):
            # Already the correct type
            return exception

        if isinstance(exception, PepperpyError):
            # Convert from one PepperPy error to another
            return cls(
                message or exception.message,
                code=exception.code,
                details=exception.details,
                cause=exception.cause,
                **kwargs,
            )

        # Convert from a standard exception
        return cls(message or str(exception), cause=exception, **kwargs)


class ValidationError(PepperpyError):
    """Error raised when validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Optional field name that failed validation
            value: Optional value that failed validation
            constraint: Optional constraint that was violated
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.field = field
        self.value = value
        self.constraint = constraint


class ConfigurationError(PepperpyError):
    """Error raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        *args,
        **kwargs,
    ):
        """Initialize configuration error.

        Args:
            message: Error message
            config_key: Optional configuration key
            config_value: Optional invalid configuration value
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


class ProviderError(PepperpyError):
    """Error raised by providers during initialization or operation."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize provider error.

        Args:
            message: Error message
            provider_name: Optional provider name
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.provider_name = provider_name
        self.operation = operation


class AuthenticationError(PepperpyError):
    """Error raised when authentication fails."""

    def __init__(self, message: str, provider: Optional[str] = None, *args, **kwargs):
        """Initialize authentication error.

        Args:
            message: Error message
            provider: Optional provider name
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.provider = provider


class AuthorizationError(PepperpyError):
    """Error raised when authorization fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize authorization error.

        Args:
            message: Error message
            provider: Optional provider name
            resource: Optional resource being accessed
            action: Optional action being performed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.provider = provider
        self.resource = resource
        self.action = action


class ResourceError(PepperpyError):
    """Error raised when a resource operation fails."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize resource error.

        Args:
            message: Error message
            resource_type: Optional resource type
            resource_id: Optional resource identifier
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.operation = operation


class NotFoundError(ResourceError):
    """Error raised when a resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize not found error.

        Args:
            message: Error message
            resource_type: Optional resource type
            resource_id: Optional resource identifier
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message,
            resource_type=resource_type,
            resource_id=resource_id,
            operation="get",
            *args,
            **kwargs,
        )


class DuplicateError(ResourceError):
    """Error raised when a duplicate resource is found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize duplicate error.

        Args:
            message: Error message
            resource_type: Optional resource type
            resource_id: Optional resource identifier
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message,
            resource_type=resource_type,
            resource_id=resource_id,
            operation="create",
            *args,
            **kwargs,
        )


class NetworkError(PepperpyError):
    """Error raised when a network operation fails."""

    def __init__(
        self,
        message: str,
        host: Optional[str] = None,
        operation: Optional[str] = None,
        status_code: Optional[int] = None,
        *args,
        **kwargs,
    ):
        """Initialize network error.

        Args:
            message: Error message
            host: Optional host name
            operation: Optional operation that failed
            status_code: Optional HTTP status code
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.host = host
        self.operation = operation
        self.status_code = status_code


class TimeoutError(NetworkError):
    """Error raised when an operation times out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Optional timeout duration
            operation: Optional operation that timed out
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, operation=operation, *args, **kwargs)
        self.timeout_seconds = timeout_seconds


class ServiceError(PepperpyError):
    """Error raised when a service operation fails."""

    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize service error.

        Args:
            message: Error message
            service_name: Optional service name
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.service_name = service_name
        self.operation = operation


class LLMError(ServiceError):
    """Error raised when an LLM operation fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize LLM error.

        Args:
            message: Error message
            provider: Optional LLM provider name
            model: Optional model name
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message, service_name=provider, operation=operation, *args, **kwargs
        )
        self.provider = provider
        self.model = model


class EmbeddingError(ServiceError):
    """Error raised when an embedding operation fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize embedding error.

        Args:
            message: Error message
            provider: Optional embedding provider name
            model: Optional model name
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message, service_name=provider, operation=operation, *args, **kwargs
        )
        self.provider = provider
        self.model = model


class RAGError(ServiceError):
    """Error raised when a RAG operation fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        index: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize RAG error.

        Args:
            message: Error message
            provider: Optional RAG provider name
            index: Optional index name
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message, service_name=provider, operation=operation, *args, **kwargs
        )
        self.provider = provider
        self.index = index


class StorageError(ServiceError):
    """Error raised when a storage operation fails."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        container: Optional[str] = None,
        path: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize storage error.

        Args:
            message: Error message
            provider: Optional storage provider name
            container: Optional container/bucket name
            path: Optional file path
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message, service_name=provider, operation=operation, *args, **kwargs
        )
        self.provider = provider
        self.container = container
        self.path = path


class ContentError(PepperpyError):
    """Error raised when a content operation fails."""

    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize content error.

        Args:
            message: Error message
            content_type: Optional content type
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.content_type = content_type
        self.operation = operation


class ParsingError(ContentError):
    """Error raised when parsing content fails."""

    def __init__(
        self,
        message: str,
        content_type: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        *args,
        **kwargs,
    ):
        """Initialize parsing error.

        Args:
            message: Error message
            content_type: Optional content type
            line: Optional line number
            column: Optional column number
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message, content_type=content_type, operation="parse", *args, **kwargs
        )
        self.line = line
        self.column = column


class ValidationErrorCollection(ValidationError):
    """Collection of validation errors."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[ValidationError]] = None,
        *args,
        **kwargs,
    ):
        """Initialize validation error collection.

        Args:
            message: Error message
            errors: Optional list of validation errors
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.errors = errors or []

    def add_error(self, error: ValidationError) -> None:
        """Add a validation error to the collection.

        Args:
            error: Validation error to add
        """
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error collection to dictionary.

        Returns:
            Dictionary representation of the error collection
        """
        result = super().to_dict()
        result["errors"] = [error.to_dict() for error in self.errors]
        return result


class PluginError(PepperpyError):
    """Error raised when a plugin operation fails."""

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        operation: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize plugin error.

        Args:
            message: Error message
            plugin_name: Optional plugin name
            operation: Optional operation that failed
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.plugin_name = plugin_name
        self.operation = operation


class PluginNotFoundError(PluginError):
    """Error raised when a plugin is not found."""

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        category: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize plugin not found error.

        Args:
            message: Error message
            plugin_name: Optional plugin name
            category: Optional plugin category
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message, plugin_name=plugin_name, operation="load", *args, **kwargs
        )
        self.category = category


class PluginInitializationError(PluginError):
    """Error raised when plugin initialization fails."""

    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        cause: Optional[Exception] = None,
        *args,
        **kwargs,
    ):
        """Initialize plugin initialization error.

        Args:
            message: Error message
            plugin_name: Optional plugin name
            cause: Optional exception that caused this error
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(
            message,
            plugin_name=plugin_name,
            operation="initialize",
            cause=cause,
            *args,
            **kwargs,
        )


class WorkflowError(PepperpyError):
    """Error raised when a workflow operation fails."""

    def __init__(
        self,
        message: str,
        workflow_name: Optional[str] = None,
        stage: Optional[str] = None,
        *args,
        **kwargs,
    ):
        """Initialize workflow error.

        Args:
            message: Error message
            workflow_name: Optional workflow name
            stage: Optional workflow stage
            *args: Additional positional arguments
            **kwargs: Additional named context values
        """
        super().__init__(message, *args, **kwargs)
        self.workflow_name = workflow_name
        self.stage = stage


class APIError(PepperpyError):
    """Error raised when an API call fails."""

    def __init__(self, message: str, status_code: int = None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        self.status_code = status_code


class RateLimitError(APIError):
    """Error raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.retry_after = retry_after


class TimeoutError(APIError):
    """Error raised when a request times out."""

    def __init__(
        self, message: str = "Request timed out", timeout: float = None, *args, **kwargs
    ):
        super().__init__(message, *args, **kwargs)
        self.timeout = timeout


class ServerError(APIError):
    """Error raised when a server error occurs."""

    def __init__(
        self, message: str = "Server error", status_code: int = 500, *args, **kwargs
    ):
        super().__init__(message, status_code, *args, **kwargs)


class NetworkError(PepperpyError):
    """Error raised when a network error occurs."""

    def __init__(
        self,
        message: str = "Network error",
        original_error: Exception = None,
        *args,
        **kwargs,
    ):
        super().__init__(message, *args, **kwargs)
        self.original_error = original_error


# Error helpers
def wrap_exception(
    exception: Exception,
    error_cls: Type[PepperpyError] = PepperpyError,
    message: Optional[str] = None,
    **kwargs,
) -> PepperpyError:
    """Wrap an exception in a PepperPy error.

    Args:
        exception: Original exception
        error_cls: PepperPy error class to use
        message: Optional custom message
        **kwargs: Additional context values

    Returns:
        PepperPy error
    """
    return error_cls.from_exception(exception, message, **kwargs)


def raise_from(
    exception: Exception,
    error_cls: Type[PepperpyError] = PepperpyError,
    message: Optional[str] = None,
    **kwargs,
) -> None:
    """Raise a PepperPy error from another exception.

    Args:
        exception: Original exception
        error_cls: PepperPy error class to use
        message: Optional custom message
        **kwargs: Additional context values

    Raises:
        PepperpyError: Wrapped exception
    """
    raise wrap_exception(exception, error_cls, message, **kwargs) from exception
