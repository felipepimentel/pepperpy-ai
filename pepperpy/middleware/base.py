"""
Base middleware interface and chain implementation.
"""

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from pepperpy.core.utils.errors import ValidationError

T = TypeVar('T')  # Type for request
R = TypeVar('R')  # Type for response

# Type alias for middleware handler
Handler = Callable[[T], Awaitable[R]]
NextHandler = Callable[[T], Awaitable[R]]


class Middleware(ABC):
    """Base class for all middleware."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the middleware.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}

    @abstractmethod
    async def process(self, request: T, next_handler: NextHandler[T, R]) -> R:
        """Process the request and call the next handler.
        
        Args:
            request: The request to process.
            next_handler: The next handler in the chain.
            
        Returns:
            The response from the chain.
        """
        raise NotImplementedError


class MiddlewareChain:
    """Chain of middleware handlers."""

    def __init__(self) -> None:
        """Initialize the middleware chain."""
        self._middleware: list[Middleware] = []

    def add(self, middleware: Middleware) -> None:
        """Add middleware to the chain.
        
        Args:
            middleware: The middleware to add.
        """
        self._middleware.append(middleware)

    def remove(self, middleware: Middleware) -> None:
        """Remove middleware from the chain.
        
        Args:
            middleware: The middleware to remove.
        """
        self._middleware.remove(middleware)

    async def execute(self, request: T, handler: Handler[T, R]) -> R:
        """Execute the middleware chain.
        
        Args:
            request: The request to process.
            handler: The final handler.
            
        Returns:
            The response from the chain.
        """
        async def create_next(
            middleware_list: list[Middleware],
            index: int,
            final_handler: Handler[T, R]
        ) -> NextHandler[T, R]:
            if index >= len(middleware_list):
                return final_handler
            
            current_middleware = middleware_list[index]
            next_middleware = await create_next(middleware_list, index + 1, final_handler)
            
            async def next_handler(req: T) -> R:
                return await current_middleware.process(req, next_middleware)
            
            return next_handler

        first_handler = await create_next(self._middleware, 0, handler)
        return await first_handler(request)


class LoggingMiddleware(Middleware):
    """Middleware for logging requests and responses."""

    async def process(self, request: T, next_handler: NextHandler[T, R]) -> R:
        """Log request and response.
        
        Args:
            request: The request to process.
            next_handler: The next handler in the chain.
            
        Returns:
            The response from the chain.
        """
        # Log request
        print(f"Request: {request}")
        
        # Process request
        response = await next_handler(request)
        
        # Log response
        print(f"Response: {response}")
        
        return response


class ValidationMiddleware(Middleware):
    """Middleware for request/response validation."""

    async def process(self, request: T, next_handler: NextHandler[T, R]) -> R:
        """Validate request and response.
        
        Args:
            request: The request to process.
            next_handler: The next handler in the chain.
            
        Returns:
            The response from the chain.
            
        Raises:
            ValidationError: If validation fails.
        """
        # Validate request
        if not self._validate_request(request):
            raise ValidationError("Invalid request")
        
        # Process request
        response = await next_handler(request)
        
        # Validate response
        if not self._validate_response(response):
            raise ValidationError("Invalid response")
        
        return response

    def _validate_request(self, request: T) -> bool:
        """Validate the request.
        
        Args:
            request: The request to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        # Implement request validation logic
        return True

    def _validate_response(self, response: R) -> bool:
        """Validate the response.
        
        Args:
            response: The response to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        # Implement response validation logic
        return True 