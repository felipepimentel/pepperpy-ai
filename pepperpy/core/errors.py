"""
PepperPy Errors.

This module provides exception classes for PepperPy, defining
a hierarchy of errors that can be raised by the framework and plugins.
"""

from typing import Any


class PepperpyError(Exception):
    """Base exception for all PepperPy errors.

    All errors in PepperPy should inherit from this class to ensure consistent
    error handling and reporting.
    """

    def __init__(
        self,
        message: str,
        *args,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
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

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary.

        Returns:
            Dictionary representation of the error
        """
        result: dict[str, Any] = {
            "type": self.__class__.__name__,
            "message": self.message,
        }

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
        cls, exception: Exception, message: str | None = None, **kwargs
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
        field: str | None = None,
        value: Any | None = None,
        constraint: str | None = None,
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
        config_key: str | None = None,
        config_value: Any | None = None,
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
        provider_name: str | None = None,
        operation: str | None = None,
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

    def __init__(self, message: str, provider: str | None = None, *args, **kwargs):
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
        provider: str | None = None,
        resource: str | None = None,
        action: str | None = None,
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
        resource_type: str | None = None,
        resource_id: str | None = None,
        operation: str | None = None,
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
        resource_type: str | None = None,
        resource_id: str | None = None,
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
        resource_type: str | None = None,
        resource_id: str | None = None,
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
        host: str | None = None,
        operation: str | None = None,
        status_code: int | None = None,
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
        timeout_seconds: float | None = None,
        operation: str | None = None,
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
        service_name: str | None = None,
        operation: str | None = None,
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
        provider: str | None = None,
        model: str | None = None,
        operation: str | None = None,
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
        provider: str | None = None,
        model: str | None = None,
        operation: str | None = None,
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
        provider: str | None = None,
        index: str | None = None,
        operation: str | None = None,
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
        provider: str | None = None,
        container: str | None = None,
        path: str | None = None,
        operation: str | None = None,
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
        content_type: str | None = None,
        operation: str | None = None,
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
        content_type: str | None = None,
        line: int | None = None,
        column: int | None = None,
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
        errors: list[ValidationError] | None = None,
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

    def to_dict(self) -> dict[str, Any]:
        """Convert error collection to dictionary.

        Returns:
            Dictionary representation of the error collection
        """
        result = super().to_dict()
        result["errors"] = [error.to_dict() for error in self.errors]
        return result


class PluginError(PepperpyError):
    """Error raised by or related to a plugin."""

    def __init__(
        self,
        message: str,
        plugin_id: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a plugin error.

        Args:
            message: Error message
            plugin_id: Optional plugin ID
            cause: Optional cause of the error
        """
        self.plugin_id = plugin_id
        message_with_id = f"[Plugin{f' {plugin_id}' if plugin_id else ''}] {message}"
        super().__init__(message_with_id, cause)


class ConfigError(PepperpyError):
    """Error related to configuration."""

    def __init__(
        self,
        message: str,
        config_path: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a configuration error.

        Args:
            message: Error message
            config_path: Optional path to the configuration
            cause: Optional cause of the error
        """
        self.config_path = config_path
        message_with_path = (
            f"[Config{f' {config_path}' if config_path else ''}] {message}"
        )
        super().__init__(message_with_path, cause)


class ApiNetworkError(PepperpyError):
    """Error related to network operations."""

    def __init__(
        self, message: str, url: str | None = None, cause: Exception | None = None
    ):
        """Initialize a network error.

        Args:
            message: Error message
            url: Optional URL that caused the error
            cause: Optional cause of the error
        """
        self.url = url
        message_with_url = f"[Network{f' {url}' if url else ''}] {message}"
        super().__init__(message_with_url, cause)


class AuthError(PepperpyError):
    """Error related to authentication."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize an authentication error.

        Args:
            message: Error message
            provider: Optional provider name
            cause: Optional cause of the error
        """
        self.provider = provider
        message_with_provider = f"[Auth{f' {provider}' if provider else ''}] {message}"
        super().__init__(message_with_provider, cause)


class DataValidationError(PepperpyError):
    """Error related to validation."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a validation error.

        Args:
            message: Error message
            field: Optional field that failed validation
            cause: Optional cause of the error
        """
        self.field = field
        message_with_field = f"[Validation{f' for {field}' if field else ''}] {message}"
        super().__init__(message_with_field, cause)


class FrameworkError(PepperpyError):
    """Error in the framework itself."""

    def __init__(
        self,
        message: str,
        component: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a framework error.

        Args:
            message: Error message
            component: Optional component name
            cause: Optional cause of the error
        """
        self.component = component
        message_with_component = (
            f"[Framework{f' {component}' if component else ''}] {message}"
        )
        super().__init__(message_with_component, cause)


# Specific plugin-related errors
class PluginInitError(PluginError):
    """Error during plugin initialization."""

    def __init__(
        self,
        message: str,
        plugin_id: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a plugin initialization error.

        Args:
            message: Error message
            plugin_id: Optional plugin ID
            cause: Optional cause of the error
        """
        super().__init__(f"Initialization error: {message}", plugin_id, cause)


class PluginNotFoundError(PluginError):
    """Error when a plugin cannot be found."""

    def __init__(
        self,
        plugin_id: str,
        plugin_type: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a plugin not found error.

        Args:
            plugin_id: Plugin ID
            plugin_type: Optional plugin type
            cause: Optional cause of the error
        """
        message = f"Plugin not found: {plugin_id}"
        if plugin_type:
            message += f" (type: {plugin_type})"
        super().__init__(message, plugin_id, cause)


class ProviderPluginError(PluginError):
    """Error in a provider plugin."""

    def __init__(
        self,
        message: str,
        provider_id: str | None = None,
        provider_type: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize a provider error.

        Args:
            message: Error message
            provider_id: Optional provider ID
            provider_type: Optional provider type
            cause: Optional cause of the error
        """
        self.provider_type = provider_type
        plugin_id = (
            f"{provider_type}/{provider_id}"
            if provider_type and provider_id
            else provider_id
        )
        super().__init__(message, plugin_id, cause)


# Error helpers
def wrap_exception(
    exception: Exception,
    error_cls: type[PepperpyError] = PepperpyError,
    message: str | None = None,
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
    error_cls: type[PepperpyError] = PepperpyError,
    message: str | None = None,
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


class PluginValidationError(ValidationError):
    """Error raised when plugin validation fails."""

    def __init__(
        self,
        message: str,
        plugin_id: str | None = None,
        plugin_type: str | None = None,
        provider_type: str | None = None,
        field: str | None = None,
        cause: Exception | None = None,
    ):
        """Initialize plugin validation error.

        Args:
            message: Error message
            plugin_id: Optional plugin ID
            plugin_type: Optional plugin type
            provider_type: Optional provider type
            field: Optional field name that failed validation
            cause: Optional exception that caused this error
        """
        super().__init__(message, field=field, cause=cause)
        self.plugin_id = plugin_id
        self.plugin_type = plugin_type
        self.provider_type = provider_type
