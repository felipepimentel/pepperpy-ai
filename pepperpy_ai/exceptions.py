"""Custom exceptions for PepperPy AI."""

from .types import JsonValue


class PepperPyAIError(Exception):
    """Base exception for PepperPy AI."""

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
        """
        super().__init__(message)
        self._message = message

    def __str__(self) -> str:
        """Get string representation."""
        return self._message


class ConfigurationError(PepperPyAIError):
    """Raised when there is a configuration error."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            field: The configuration field that caused the error.
        """
        super().__init__(message)
        self.field = field


class ProviderError(PepperPyAIError):
    """Raised when there is an error with an AI provider."""

    def __init__(self, message: str, provider: str) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            provider: The name of the provider that caused the error.
        """
        super().__init__(message)
        self.provider = provider


class ValidationError(PepperPyAIError):
    """Raised when there is a validation error."""

    def __init__(self, message: str, field: str, value: JsonValue) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            field: The field that failed validation.
            value: The invalid value.
        """
        super().__init__(message)
        self.field = field
        self.value = value


class CapabilityError(PepperPyAIError):
    """Raised when there is an error with an AI capability."""

    def __init__(self, message: str, capability: str) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            capability: The name of the capability that caused the error.
        """
        super().__init__(message)
        self.capability = capability


class DependencyError(PepperPyAIError):
    """Raised when there is a missing or incompatible dependency."""

    def __init__(self, message: str, package: str) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            package: The name of the package that is missing or incompatible.
        """
        super().__init__(message)
        self.package = package


class EmbeddingsError(Exception):
    """Base class for embeddings errors."""

    def __init__(self, message: str) -> None:
        """Initialize error.

        Args:
            message: Error message
        """
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Get string representation."""
        return self.message


class TemplateError(PepperPyAIError):
    """Raised when there is a template error."""

    def __init__(self, message: str, operation: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message.
            operation: Operation that failed.
        """
        super().__init__(message)
        self.operation = operation
