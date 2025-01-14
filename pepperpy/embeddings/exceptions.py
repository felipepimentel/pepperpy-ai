"""Embeddings exceptions module."""

from ..exceptions import PepperPyAIError


class EmbeddingError(PepperPyAIError):
    """Base class for embeddings errors."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize error.

        Args:
            message: Error message.
            cause: Original exception that caused this error.
        """
        super().__init__(message)
        self.cause = cause

    def __eq__(self, other: object) -> bool:
        """Compare error with another object.

        Args:
            other: Object to compare with.

        Returns:
            bool: True if objects are equal, False otherwise.
        """
        if not isinstance(other, EmbeddingError):
            return NotImplemented
        return (
            str(self) == str(other)
            and isinstance(other, type(self))
            and self.cause == other.cause
        )


class ConfigurationError(EmbeddingError):
    """Configuration error."""


class ProviderError(EmbeddingError):
    """Provider error."""


class CacheError(EmbeddingError):
    """Cache error."""
