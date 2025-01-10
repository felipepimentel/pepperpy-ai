"""Embedding exceptions module"""

from typing import Any


class EmbeddingError(Exception):
    """Base exception for embedding errors"""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize embedding error

        Args:
            message: Error message
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self._message = message
        self._cause = cause

    @property
    def message(self) -> str:
        """Get error message"""
        return self._message

    @property
    def cause(self) -> Exception | None:
        """Get original exception"""
        return self._cause

    def __str__(self) -> str:
        """Get string representation"""
        return self._message

    def __repr__(self) -> str:
        """Get detailed string representation"""
        return f"EmbeddingError('{self._message}')"

    def __eq__(self, other: Any) -> bool:
        """Check equality"""
        if not isinstance(other, EmbeddingError):
            return False
        return self._message == other._message

    def __hash__(self) -> int:
        """Get hash value"""
        return hash(self._message)


class ConfigurationError(EmbeddingError):
    """Configuration error"""


class ProviderError(EmbeddingError):
    """Provider error"""


class CacheError(EmbeddingError):
    """Cache error"""
