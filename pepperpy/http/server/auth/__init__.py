"""HTTP server authentication module.

This module provides authentication for HTTP server.
"""

from typing import Callable, Dict, List, Optional, Union

from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    SimpleUser,
    UnauthenticatedUser,
)
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request

__all__ = [
    "AuthCredentials",
    "AuthenticationBackend",
    "AuthenticationError",
    "AuthenticationMiddleware",
    "SimpleUser",
    "UnauthenticatedUser",
]
