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
from collections.abc import Callable
from typing import Any

from pepperpy.core.errors.unified import PepperError

logger = logging.getLogger(__name__)


class ErrorHandler(ABC):
    """Base class for error handlers."""

    @abstractmethod
    def handle(self, error: Exception) -> Any:
        """Handle an error.

        Args:
            error: The error to handle

        Returns:
            Any: The result of handling the error
        """
        raise NotImplementedError


class DefaultErrorHandler(ErrorHandler):
    """Default error handler that provides basic error handling."""

    def handle(self, error: Exception) -> Any:
        """Handle an error with default behavior.

        Args:
            error: The error to handle

        Returns:
            Any: The result of handling the error
        """
        if isinstance(error, PepperError):
            # Handle framework errors
            return {
                "error": error.__class__.__name__,
                "message": str(error),
                "code": getattr(error, "code", None),
            }

        # Handle unexpected errors
        return {"error": "UnexpectedError", "message": str(error), "code": None}


class ChainedErrorHandler(ErrorHandler):
    """Chain multiple error handlers together."""

    def __init__(self, handlers: list[ErrorHandler] | None = None):
        """Initialize the chained handler.

        Args:
            handlers: List of handlers to chain together
        """
        self.handlers = handlers or []

    def add_handler(self, handler: ErrorHandler) -> None:
        """Add a handler to the chain.

        Args:
            handler: The handler to add
        """
        self.handlers.append(handler)

    def handle(self, error: Exception) -> Any:
        """Try each handler in the chain until one succeeds.

        Args:
            error: The error to handle

        Returns:
            Any: The result from the first successful handler

        Raises:
            Exception: If no handler can handle the error
        """
        for handler in self.handlers:
            try:
                return handler.handle(error)
            except Exception:
                continue

        # If no handler worked, use default
        return DefaultErrorHandler().handle(error)


class ErrorMiddleware:
    """Middleware for handling errors in the request/response cycle."""

    def __init__(
        self,
        handler: ErrorHandler | None = None,
        error_types: list[type[Exception]] | None = None,
    ):
        """Initialize the middleware.

        Args:
            handler: The error handler to use
            error_types: List of error types to handle
        """
        self.handler = handler or DefaultErrorHandler()
        self.error_types = error_types or [Exception]

    def __call__(self, func: Callable) -> Callable:
        """Wrap a function with error handling.

        Args:
            func: The function to wrap

        Returns:
            Callable: The wrapped function
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if any(isinstance(e, t) for t in self.error_types):
                    return self.handler.handle(e)
                raise

        return wrapper


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
                if handler.handle(error):
                    return True
            except Exception as e:
                logger.error(f"Handler {handler.__class__.__name__} failed: {e}")
        return False


# Global error handler registry
global_error_registry = ErrorHandlerRegistry()
