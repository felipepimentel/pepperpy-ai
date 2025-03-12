"""HTTP module.

This module provides functionality for HTTP client and server.
"""

# Connection pooling
from pepperpy.http.client import (
    HTTPClient,
    HTTPClientContext,
    HTTPConnectionPool,
    HTTPPoolConfig,
    HTTPXClient,
    RequestOptions,
    create_http_pool,
    get_http_client,
    get_http_pool,
    http_client,
    initialize_default_http_pool,
    release_http_client,
)
from pepperpy.http.client import (
    Response as ClientResponse,
)
from pepperpy.http.client import (
    delete as client_delete,
)
from pepperpy.http.client import (
    get as client_get,
)
from pepperpy.http.client import (
    head as client_head,
)
from pepperpy.http.client import (
    options as client_options,
)
from pepperpy.http.client import (
    patch as client_patch,
)
from pepperpy.http.client import (
    post as client_post,
)
from pepperpy.http.client import (
    put as client_put,
)
from pepperpy.http.client import (
    request as client_request,
)
from pepperpy.http.errors import (
    AuthenticationError,
    AuthorizationError,
    ClientError,
    ConnectionError,
    HandlerError,
    HTTPError,
    MiddlewareError,
    RequestError,
    ResponseError,
    RoutingError,
    ServerError,
    TimeoutError,
)
from pepperpy.http.utils import (
    check_status_code,
    format_headers,
    get_content_type,
    is_json_content,
    parse_json,
    parse_query_params,
)

# Try to import server components, but make them optional
try:
    from pepperpy.http.server import (
        FunctionHandler,
        Handler,
        JSONHandler,
        Router,
        Server,
        ServerOptions,
        add_route,
        get_router,
        get_server,
        set_server,
    )
    from pepperpy.http.server import (
        delete as server_delete,
    )
    from pepperpy.http.server import (
        get as server_get,
    )
    from pepperpy.http.server import (
        head as server_head,
    )
    from pepperpy.http.server import (
        options as server_options,
    )
    from pepperpy.http.server import (
        patch as server_patch,
    )
    from pepperpy.http.server import (
        post as server_post,
    )
    from pepperpy.http.server import (
        put as server_put,
    )
    from pepperpy.http.server import (
        start as server_start,
    )
    from pepperpy.http.server import (
        stop as server_stop,
    )

    _server_available = True
except ImportError:
    _server_available = False

__all__ = [
    # Client
    "HTTPClient",
    "HTTPXClient",
    "RequestOptions",
    "ClientResponse",
    "client_delete",
    "client_get",
    "client_head",
    "client_options",
    "client_patch",
    "client_post",
    "client_put",
    "client_request",
    "get_http_client",
    # Connection pooling
    "HTTPClientContext",
    "HTTPConnectionPool",
    "HTTPPoolConfig",
    "create_http_pool",
    "get_http_pool",
    "http_client",
    "initialize_default_http_pool",
    "release_http_client",
    # Errors
    "AuthenticationError",
    "AuthorizationError",
    "ClientError",
    "ConnectionError",
    "HTTPError",
    "HandlerError",
    "MiddlewareError",
    "RequestError",
    "ResponseError",
    "RoutingError",
    "ServerError",
    "TimeoutError",
    # Utils
    "check_status_code",
    "format_headers",
    "get_content_type",
    "is_json_content",
    "parse_json",
    "parse_query_params",
]

# Add server components to __all__ if available
if _server_available:
    __all__.extend([
        # Server
        "FunctionHandler",
        "Handler",
        "JSONHandler",
        "Router",
        "Server",
        "ServerOptions",
        "add_route",
        "server_delete",
        "server_get",
        "get_router",
        "get_server",
        "server_head",
        "server_options",
        "server_patch",
        "server_post",
        "server_put",
        "set_server",
        "server_start",
        "server_stop",
    ])
