"""HTTP error handling utilities."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import ClientError, ServerError


@dataclass
class HTTPError(Exception):
    """HTTP error details."""
    
    status_code: int
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary.
        
        Returns:
            Dict[str, Any]: Error details as dictionary.
        """
        error_dict = {
            "status_code": self.status_code,
            "message": self.message,
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict


class BadRequestError(ClientError):
    """400 Bad Request error."""
    
    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(400, message, details)


class UnauthorizedError(ClientError):
    """401 Unauthorized error."""
    
    def __init__(
        self,
        message: str = "Unauthorized",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(401, message, details)


class ForbiddenError(ClientError):
    """403 Forbidden error."""
    
    def __init__(
        self,
        message: str = "Forbidden",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(403, message, details)


class NotFoundError(ClientError):
    """404 Not Found error."""
    
    def __init__(
        self,
        message: str = "Not found",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(404, message, details)


class ConflictError(ClientError):
    """409 Conflict error."""
    
    def __init__(
        self,
        message: str = "Conflict",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(409, message, details)


class InternalServerError(ServerError):
    """500 Internal Server Error."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(500, message, details)


class ServiceUnavailableError(ServerError):
    """503 Service Unavailable error."""
    
    def __init__(
        self,
        message: str = "Service unavailable",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.http_error = HTTPError(503, message, details) 