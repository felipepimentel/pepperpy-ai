"""Error classes for PepperPy.

This module provides error classes used throughout the PepperPy framework.
"""


class PepperpyError(Exception):
    """Base class for all PepperPy exceptions.

    All custom exceptions in PepperPy should inherit from this class.
    """

    def __init__(self, message: str, *args, **kwargs):
        """Initialize a PepperPy error.

        Args:
            message: Error message
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(message, *args)
        self.message = message
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            Error message
        """
        return self.message
