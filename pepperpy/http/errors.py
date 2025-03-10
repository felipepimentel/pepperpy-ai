"""Error classes for the HTTP module.

This module defines error classes specific to HTTP operations.
"""

from typing import Any, Dict, Optional

from pepperpy.errors import PepperPyError


class HTTPError(PepperPyError):
    """Base class for HTTP-related errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize an HTTP error.

        Args:
            message: The error message
            status_code: The HTTP status code
            details: Additional details about the error
        """
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class ClientError(HTTPError):
    """Error raised when there is an issue with an HTTP client."""

    pass


class ServerError(HTTPError):
    """Error raised when there is an issue with an HTTP server."""

    pass


class RequestError(ClientError):
    """Error raised when there is an issue with an HTTP request."""

    pass


class ResponseError(ClientError):
    """Error raised when there is an issue with an HTTP response."""

    pass


class ConnectionError(ClientError):
    """Error raised when there is an issue with an HTTP connection."""

    pass


class TimeoutError(ClientError):
    """Error raised when an HTTP request times out."""

    pass


class AuthenticationError(ClientError):
    """Error raised when there is an authentication issue."""

    pass


class AuthorizationError(ClientError):
    """Error raised when there is an authorization issue."""

    pass


class RoutingError(ServerError):
    """Error raised when there is an issue with HTTP routing."""

    pass


class MiddlewareError(ServerError):
    """Error raised when there is an issue with HTTP middleware."""

    pass


class HandlerError(ServerError):
    """Error raised when there is an issue with an HTTP handler."""

    pass
