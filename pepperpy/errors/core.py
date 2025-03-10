"""Core exceptions for PepperPy.

This module provides the core exceptions for the PepperPy framework,
including base exceptions and common error types that are used throughout the framework.
"""

from typing import Any, Dict, Optional, Type


class PepperPyError(Exception):
    """Base exception for all PepperPy errors.

    All exceptions in the PepperPy framework should inherit from this exception.
    """

    def __init__(self, message: str, **kwargs: Any):
        """Initialize a PepperPy error.

        Args:
            message: The error message
            **kwargs: Additional error metadata
        """
        self.message = message
        self.metadata = kwargs
        super().__init__(message)

    def __str__(self) -> str:
        """Get a string representation of the error.

        Returns:
            A string representation of the error
        """
        return self.message


class ConfigError(PepperPyError):
    """Base exception for all configuration errors.

    This exception is raised when there is an error with the configuration.
    """

    pass


class ValidationError(PepperPyError):
    """Exception for validation errors.

    This exception is raised when validation of an object fails.
    """

    def __init__(
        self, message: str, errors: Optional[Dict[str, str]] = None, **kwargs: Any
    ):
        """Initialize a validation error.

        Args:
            message: The error message
            errors: A dictionary of field-specific errors
            **kwargs: Additional error metadata
        """
        self.errors = errors or {}
        super().__init__(message, errors=self.errors, **kwargs)

    def __str__(self) -> str:
        """Get a string representation of the error.

        Returns:
            A string representation of the error
        """
        error_str = self.message

        if self.errors:
            error_str += "\n" + "\n".join(
                f"  {field}: {error}" for field, error in self.errors.items()
            )

        return error_str


class NotFoundError(PepperPyError):
    """Exception for not found errors.

    This exception is raised when a requested resource is not found.
    """

    pass


class AuthenticationError(PepperPyError):
    """Exception for authentication errors.

    This exception is raised when authentication fails.
    """

    pass


class AuthorizationError(PepperPyError):
    """Exception for authorization errors.

    This exception is raised when authorization fails.
    """

    pass


class NetworkError(PepperPyError):
    """Exception for network errors.

    This exception is raised when there is a network error.
    """

    pass


class TimeoutError(PepperPyError):
    """Exception for timeout errors.

    This exception is raised when an operation times out.
    """

    pass


class RateLimitError(PepperPyError):
    """Exception for rate limit errors.

    This exception is raised when a rate limit is exceeded.
    """

    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs: Any):
        """Initialize a rate limit error.

        Args:
            message: The error message
            retry_after: The number of seconds to wait before retrying
            **kwargs: Additional error metadata
        """
        self.retry_after = retry_after
        super().__init__(message, retry_after=retry_after, **kwargs)


class ProviderError(PepperPyError):
    """Exception for provider errors.

    This exception is raised when there is an error with a provider.
    """

    pass


class SerializationError(PepperPyError):
    """Exception for serialization errors.

    This exception is raised when serialization or deserialization fails.
    """

    pass


class ImportError(PepperPyError):
    """Exception for import errors.

    This exception is raised when a required dependency is not installed.
    """

    def __init__(self, message: str, package: Optional[str] = None, **kwargs: Any):
        """Initialize an import error.

        Args:
            message: The error message
            package: The name of the package that could not be imported
            **kwargs: Additional error metadata
        """
        self.package = package
        super().__init__(message, package=package, **kwargs)


class ConfigValidationError(ValidationError, ConfigError):
    """Exception for configuration validation errors.

    This exception is raised when validation of a configuration fails.
    """

    pass


class ConfigNotFoundError(NotFoundError, ConfigError):
    """Exception for configuration not found errors.

    This exception is raised when a requested configuration is not found.
    """

    pass


class PipelineError(PepperPyError):
    """Exception for pipeline errors.

    This exception is raised when there is an error in a pipeline.
    """

    pass


class PipelineStageError(PipelineError):
    """Exception for pipeline stage errors.

    This exception is raised when there is an error in a pipeline stage.
    """

    def __init__(self, message: str, stage_name: Optional[str] = None, **kwargs: Any):
        """Initialize a pipeline stage error.

        Args:
            message: The error message
            stage_name: The name of the stage that failed
            **kwargs: Additional error metadata
        """
        self.stage_name = stage_name
        super().__init__(message, stage_name=stage_name, **kwargs)


def convert_exception(exception: Exception, target_class: Type[Exception]) -> Exception:
    """Convert an exception to a different type.

    Args:
        exception: The exception to convert
        target_class: The target exception class

    Returns:
        The converted exception
    """
    if isinstance(exception, target_class):
        return exception

    # Create a new instance of the target class
    if isinstance(exception, PepperPyError):
        # If the source exception is a PepperPyError, preserve metadata
        message = exception.message
        new_exception = target_class(message, **exception.metadata)
    else:
        # Otherwise, use the string representation as the message
        message = str(exception)
        new_exception = target_class(message)

    # Set the cause of the new exception to the original exception
    new_exception.__cause__ = exception

    return new_exception


def wrap_exception(
    exception: Exception, wrapper_class: Type[Exception], message: Optional[str] = None
) -> Exception:
    """Wrap an exception in another exception.

    Args:
        exception: The exception to wrap
        wrapper_class: The wrapper exception class
        message: The message for the wrapper exception, or None to use the original message

    Returns:
        The wrapped exception
    """
    if message is None:
        message = str(exception)

    # Create a new instance of the wrapper class
    new_exception = wrapper_class(message)

    # Set the cause of the new exception to the original exception
    new_exception.__cause__ = exception

    return new_exception
