"""HTTP server module.

This module provides functionality for serving HTTP requests.
"""

from pepperpy.http.server.auth import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    AuthenticationMiddleware,
    SimpleUser,
    UnauthenticatedUser,
)
from pepperpy.http.server.core import (
    FunctionHandler,
    Handler,
    JSONHandler,
    Router,
    Server,
    ServerOptions,
    add_route,
    delete,
    get,
    get_router,
    get_server,
    head,
    options,
    patch,
    post,
    put,
    set_server,
    start,
    stop,
)
from pepperpy.http.server.middleware import (
    CORSMiddleware,
    GZipMiddleware,
    HTTPSRedirectMiddleware,
    Middleware,
    TrustedHostMiddleware,
)

__all__ = [
    # Core
    "FunctionHandler",
    "Handler",
    "JSONHandler",
    "Router",
    "Server",
    "ServerOptions",
    "add_route",
    "delete",
    "get",
    "get_router",
    "get_server",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "set_server",
    "start",
    "stop",
    # Auth
    "AuthCredentials",
    "AuthenticationBackend",
    "AuthenticationError",
    "AuthenticationMiddleware",
    "SimpleUser",
    "UnauthenticatedUser",
    # Middleware
    "Middleware",
    "CORSMiddleware",
    "GZipMiddleware",
    "HTTPSRedirectMiddleware",
    "TrustedHostMiddleware",
]
