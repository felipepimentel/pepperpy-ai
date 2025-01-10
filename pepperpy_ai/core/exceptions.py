"""Exceptions for pepperpy-ai."""


class PepperpyError(Exception):
    """Base exception for pepperpy-ai."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize exception."""
        super().__init__(message)
        self.cause = cause
