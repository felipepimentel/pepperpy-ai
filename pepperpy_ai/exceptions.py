"""Custom exceptions."""


class PepperpyError(Exception):
    """Base exception for PepperPy errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize exception.

        Args:
            message: Error message
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.cause = cause


class AIError(PepperpyError):
    """AI operation error."""

    pass


class ConfigError(PepperpyError):
    """Configuration error."""

    pass


class ProviderError(PepperpyError):
    """Provider error."""

    pass
