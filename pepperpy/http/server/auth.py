"""HTTP server authentication module.

This module provides authentication for HTTP server.
"""

from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
    UnauthenticatedUser,
)
from starlette.middleware.authentication import AuthenticationMiddleware

__all__ = [
    "AuthCredentials",
    "AuthenticationBackend",
    "AuthenticationError",
    "AuthenticationMiddleware",
    "SimpleUser",
    "UnauthenticatedUser",
]
