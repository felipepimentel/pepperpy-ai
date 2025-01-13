"""Exception classes for PepperPy AI."""

from typing import Any


class PepperPyAIError(Exception):
    """Base exception for all PepperPy AI errors."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            **kwargs: Additional context
        """
        super().__init__(message)
        self.context = kwargs


class ConfigurationError(PepperPyAIError):
    """Configuration error."""


class ValidationError(PepperPyAIError):
    """Validation error."""


class ProviderError(PepperPyAIError):
    """Provider error."""

    def __init__(
        self,
        message: str,
        provider: str,
        operation: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            provider: Provider name
            operation: Operation that failed
            cause: Original exception
        """
        super().__init__(
            message,
            provider=provider,
            operation=operation,
            cause=str(cause) if cause else None,
        )


class CapabilityError(PepperPyAIError):
    """Capability error."""

    def __init__(
        self,
        message: str,
        capability: str,
        operation: str,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            capability: Capability name
            operation: Operation that failed
            cause: Original exception
        """
        super().__init__(
            message,
            capability=capability,
            operation=operation,
            cause=str(cause) if cause else None,
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
            feature: Feature that requires the dependency
            package: Package that is missing
            extra: Optional extra to install
            **kwargs: Additional context
        """
        pip_install = (
            f"pip install {package}"
            if not extra
            else f"pip install pepperpy-ai[{extra}]"
        )

        message = (
            f"\n\nThe feature '{feature}' requires the '{package}' package "
            "which is not installed.\n"
            f"To use this feature, install the required dependency using pip:\n\n"
            f"    {pip_install}\n\n"
        )

        super().__init__(
            message,
            feature=feature,
            package=package,
            extra=extra,
            **kwargs,
        )
