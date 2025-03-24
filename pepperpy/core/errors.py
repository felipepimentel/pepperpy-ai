"""Base error classes for PepperPy."""

class PepperPyError(Exception):
    """Base class for all PepperPy errors."""

    def __init__(self, message: str) -> None:
        """Initialize the error.

        Args:
            message: The error message.
        """
        super().__init__(message)
        self.message = message 