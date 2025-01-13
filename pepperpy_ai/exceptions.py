"""Exceptions module."""

from typing import Any


class PepperPyAIError(Exception):
    """Base exception for all PepperPy AI errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            **kwargs: Additional error context
        """
        super().__init__(message)
        self.context = kwargs if kwargs else {}


class ConfigurationError(PepperPyAIError):
    """Configuration error."""


class ProviderError(PepperPyAIError):
    """Provider error."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        operation: str | None = None,
        cause: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize provider error.

        Args:
            message: Error message
            provider: Provider name
            operation: Operation that failed
            cause: Original exception
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            provider=provider,
            operation=operation,
            cause=cause,
            **kwargs,
        )


class ValidationError(PepperPyAIError):
    """Validation error."""


class CapabilityError(PepperPyAIError):
    """Capability error."""

    def __init__(
        self,
        message: str,
        capability: str | None = None,
        operation: str | None = None,
        cause: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize capability error.

        Args:
            message: Error message
            capability: Capability name
            operation: Operation that failed
            cause: Original exception
            **kwargs: Additional error context
        """
        super().__init__(
            message,
            capability=capability,
            operation=operation,
            cause=cause,
            **kwargs,
        )


class DependencyError(PepperPyAIError):
    """Dependency error."""

    def __init__(
        self,
        feature: str,
        package: str,
        extra: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception.

        Args:
            feature: Feature requiring the dependency
            package: Required package
            extra: Optional extra containing the package
            **kwargs: Additional error context
        """
        message = f"{feature} requires {package}"
        if extra:
            message += f" (install with pip install pepperpy-ai[{extra}])"
        super().__init__(
            message,
            feature=feature,
            package=package,
            extra=extra,
            **kwargs,
        )
