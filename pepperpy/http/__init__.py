"""
PepperPy HTTP Module.

This module provides HTTP client and server functionality for the PepperPy framework.
"""

# Import client functionality
from pepperpy.http.client import (
    HTTPClient,
    RequestOptions,
    Response,
    delete,
    get,
    get_http_client,
    head,
    options,
    patch,
    post,
    put,
    request,
    set_http_client,
)

# Import errors
from pepperpy.http.errors import (
    ConnectionError,
    HTTPError,
    RequestError,
    ResponseError,
    TimeoutError,
)

# Define exports
__all__ = [
    # Client
    "HTTPClient",
    "RequestOptions",
    "Response",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "request",
    "get_http_client",
    "set_http_client",
    # Errors
    "HTTPError",
    "RequestError",
    "ResponseError",
    "ConnectionError",
    "TimeoutError",
]

# Try to import server functionality, but don't fail if not available
try:
    import sys

    if "pepperpy.http.server" in sys.modules:
        from pepperpy.http.server import *

        __all__.extend(sys.modules["pepperpy.http.server"].__all__)
except (ImportError, AttributeError):
    pass
