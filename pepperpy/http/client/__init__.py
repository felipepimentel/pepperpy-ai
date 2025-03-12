"""HTTP client module.

This module provides functionality for making HTTP requests.
"""

from pepperpy.http.client.core import (
    HTTPClient,
    HTTPXClient,
    RequestOptions,
    Response,
)
from pepperpy.http.client.pool import (
    HTTPClientContext,
    HTTPConnectionPool,
    HTTPPoolConfig,
    create_http_pool,
    delete,
    get,
    get_http_client,
    get_http_pool,
    head,
    http_client,
    initialize_default_http_pool,
    options,
    patch,
    post,
    put,
    release_http_client,
    request,
)

__all__ = [
    # Core classes
    "HTTPClient",
    "HTTPXClient",
    "RequestOptions",
    "Response",
    # Connection pooling
    "HTTPConnectionPool",
    "HTTPPoolConfig",
    "HTTPClientContext",
    "create_http_pool",
    "get_http_pool",
    "get_http_client",
    "release_http_client",
    "initialize_default_http_pool",
    "http_client",
    # Request functions
    "request",
    "get",
    "post",
    "put",
    "delete",
    "head",
    "options",
    "patch",
]
