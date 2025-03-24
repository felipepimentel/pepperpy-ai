"""Embedding errors for PepperPy.

This module defines embedding-specific errors for the PepperPy framework.
"""

from typing import Any, Optional

from pepperpy.core.errors import PepperPyError


class EmbeddingError(PepperPyError):
    """Base class for embedding errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize an embedding error.

        Args:
            message: Error message
            provider: Optional provider name
            model: Optional model name
            **kwargs: Additional error context
        """
        super().__init__(message, **kwargs)
        self.provider = provider
        self.model = model

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Error message with provider and model if available
        """
        parts = [self.message]
        if self.provider:
            parts.append(f"Provider: {self.provider}")
        if self.model:
            parts.append(f"Model: {self.model}")
        return " | ".join(parts) 