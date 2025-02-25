"""Base classes for error handling in Pepperpy.

This module provides the core error handling functionality, including:
- Abstract error handler interface
- Error handler registry
- Common error handling patterns

Example:
    >>> registry = ErrorHandlerRegistry()
    >>> handler = MyHandler()
    >>> registry.register(ValidationError, handler)
    >>> error = ValidationError("Invalid input")
    >>> registry.handle(error)
    True
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ErrorHandler(ABC):
    """Abstract base class for error handlers.

    All error handlers must implement can_handle and handle methods.

    Example:
        >>> class MyHandler(ErrorHandler):
        ...     def can_handle(self, error):
        ...         return isinstance(error, ValidationError)
        ...     def handle(self, error):
        ...         logger.error(f"Validation error: {error}")
        ...         return True
    """

    @abstractmethod
    def can_handle(self, error: Exception) -> bool:
        """Check if this handler can handle the given error.

        Args:
            error: The error to check

        Returns:
            bool: True if this handler can handle the error
        """
        pass

    @abstractmethod
    def handle(self, error: Exception) -> bool:
        """Handle the given error.

        Args:
            error: The error to handle

        Returns:
            bool: True if the error was handled successfully

        Raises:
            Any: Implementation may raise additional errors
        """
        pass


class ErrorHandlerRegistry:
    """Registry for error handlers.

    Maintains a mapping of error types to their handlers and provides
    methods for registering and executing handlers.

    Example:
        >>> registry = ErrorHandlerRegistry()
        >>> handler = MyHandler()
        >>> registry.register(ValidationError, handler)
        >>> error = ValidationError("Invalid input")
        >>> registry.handle(error)
        True
    """

    def __init__(self) -> None:
        """Initialize a new error handler registry."""
        self._handlers: dict[type[Exception], list[ErrorHandler]] = {}

    def register(self, error_type: type[Exception], handler: ErrorHandler) -> None:
        """Register a handler for an error type.

        Args:
            error_type: The type of error to handle
            handler: The handler to register

        Example:
            >>> registry = ErrorHandlerRegistry()
            >>> handler = MyHandler()
            >>> registry.register(ValidationError, handler)
        """
        if error_type not in self._handlers:
            self._handlers[error_type] = []
        self._handlers[error_type].append(handler)

    def unregister(self, error_type: type[Exception], handler: ErrorHandler) -> None:
        """Unregister a handler for an error type.

        Args:
            error_type: The type of error
            handler: The handler to unregister

        Example:
            >>> registry.unregister(ValidationError, handler)
        """
        if error_type in self._handlers:
            self._handlers[error_type].remove(handler)
            if not self._handlers[error_type]:
                del self._handlers[error_type]

    def get_handlers(self, error_type: type[Exception]) -> list[ErrorHandler]:
        """Get all handlers for an error type.

        Includes handlers registered for parent error types.

        Args:
            error_type: The type of error

        Returns:
            List[ErrorHandler]: List of handlers for the error type

        Example:
            >>> handlers = registry.get_handlers(ValidationError)
            >>> len(handlers)
            1
        """
        handlers = []
        for t in error_type.__mro__:
            if t in self._handlers:
                handlers.extend(self._handlers[t])
        return handlers

    def handle(self, error: Exception) -> bool:
        """Handle an error using registered handlers.

        Args:
            error: The error to handle

        Returns:
            bool: True if the error was handled successfully

        Example:
            >>> error = ValidationError("Invalid input")
            >>> registry.handle(error)
            True
        """
        handlers = self.get_handlers(type(error))
        for handler in handlers:
            try:
                if handler.can_handle(error):
                    if handler.handle(error):
                        return True
            except Exception as e:
                logger.error(f"Handler {handler.__class__.__name__} failed: {e}")
        return False


# Global error handler registry
global_error_registry = ErrorHandlerRegistry()
