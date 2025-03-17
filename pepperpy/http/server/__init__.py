"""HTTP server module.

This module provides functionality for serving HTTP requests.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from pepperpy.http.errors import HandlerError
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

from pepperpy.http.server.auth import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
    AuthenticationMiddleware,
    SimpleUser,
    UnauthenticatedUser,
)
from pepperpy.http.server.middleware import (
    CORSMiddleware,
    GZipMiddleware,
    HTTPSRedirectMiddleware,
    Middleware,
    TrustedHostMiddleware,
)


@dataclass
class ServerOptions:
    """Options for HTTP server.

    Attributes:
        host: The host to bind to
        port: The port to bind to
        debug: Whether to enable debug mode
        log_level: The log level to use
        middleware: Middleware to use
        cors: CORS configuration
        ssl_certfile: Path to SSL certificate file
        ssl_keyfile: Path to SSL key file
    """

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    log_level: int = logging.INFO
    middleware: List[Middleware] = field(default_factory=list)
    cors: Optional[Dict[str, Any]] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None


class Handler(ABC):
    """Base class for HTTP request handlers.

    HTTP request handlers are responsible for handling HTTP requests and
    returning HTTP responses.
    """

    @abstractmethod
    async def handle(self, request: Request) -> Response:
        """Handle an HTTP request.

        Args:
            request: The HTTP request to handle

        Returns:
            The HTTP response

        Raises:
            HandlerError: If there is an error handling the request
        """
        pass


class JSONHandler(Handler):
    """Base class for JSON request handlers.

    JSON request handlers are responsible for handling HTTP requests and
    returning JSON responses.
    """

    @abstractmethod
    async def handle_json(self, request: Request) -> Dict[str, Any]:
        """Handle an HTTP request and return JSON data.

        Args:
            request: The HTTP request to handle

        Returns:
            The JSON data to return

        Raises:
            HandlerError: If there is an error handling the request
        """
        pass

    async def handle(self, request: Request) -> Response:
        """Handle an HTTP request.

        Args:
            request: The HTTP request to handle

        Returns:
            The HTTP response

        Raises:
            HandlerError: If there is an error handling the request
        """
        try:
            data = await self.handle_json(request)
            return JSONResponse(data)
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            raise HandlerError(f"Error handling request: {str(e)}") from e


class FunctionHandler(Handler):
    """Handler that wraps a function.

    This handler wraps a function that takes a request and returns a response.
    """

    def __init__(self, func: Callable[[Request], Response]):
        """Initialize the handler.

        Args:
            func: The function to wrap
        """
        self.func = func

    async def handle(self, request: Request) -> Response:
        """Handle an HTTP request.

        Args:
            request: The HTTP request to handle

        Returns:
            The HTTP response

        Raises:
            HandlerError: If there is an error handling the request
        """
        try:
            # Call the function
            result = self.func(request)

            # If the result is a coroutine, await it
            if asyncio.iscoroutine(result):
                result = await result

            return result
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            raise HandlerError(f"Error handling request: {str(e)}") from e


class Router:
    """HTTP router.

    The router is responsible for routing HTTP requests to handlers.
    """

    def __init__(self):
        """Initialize the router."""
        self.routes: List[Route] = []

    def add_route(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Add a route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            methods: The HTTP methods to route
            name: The name of the route
        """
        # If the handler is a function, wrap it in a FunctionHandler
        if not isinstance(handler, Handler):
            handler = FunctionHandler(handler)

        # Create a Starlette route
        route = Route(
            path,
            endpoint=handler.handle,
            methods=methods,
            name=name,
        )

        # Add the route to the router
        self.routes.append(route)

    def get(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add a GET route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["GET"], name=name)

    def post(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add a POST route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["POST"], name=name)

    def put(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add a PUT route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["PUT"], name=name)

    def delete(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add a DELETE route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["DELETE"], name=name)

    def patch(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add a PATCH route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["PATCH"], name=name)

    def head(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add a HEAD route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["HEAD"], name=name)

    def options(
        self,
        path: str,
        handler: Union[Handler, Callable[[Request], Response]],
        name: Optional[str] = None,
    ) -> None:
        """Add an OPTIONS route to the router.

        Args:
            path: The path to route
            handler: The handler to route to
            name: The name of the route
        """
        self.add_route(path, handler, methods=["OPTIONS"], name=name)


class Server:
    """HTTP server.

    The server is responsible for serving HTTP requests.
    """

    def __init__(
        self,
        router: Optional[Router] = None,
        options: Optional[ServerOptions] = None,
    ):
        """Initialize the server.

        Args:
            router: The router to use
            options: The server options
        """
        self.router = router or Router()
        self.options = options or ServerOptions()
        self.app: Optional[Starlette] = None
        self.server = None
        self.running = False

    def build_app(self) -> Starlette:
        """Build the Starlette application.

        Returns:
            The Starlette application
        """
        # Create the application
        app = Starlette(
            debug=self.options.debug,
            routes=self.router.routes,
            middleware=self.options.middleware,
        )

        return app

    async def start(self) -> None:
        """Start the server."""
        if self.running:
            logger.warning("Server is already running")
            return

        # Build the application
        self.app = self.build_app()

        # Configure logging
        logging.basicConfig(level=self.options.log_level)

        # Start the server
        import uvicorn

        config = uvicorn.Config(
            app=self.app,
            host=self.options.host,
            port=self.options.port,
            log_level=logging.getLevelName(self.options.log_level).lower(),
            ssl_certfile=self.options.ssl_certfile,
            ssl_keyfile=self.options.ssl_keyfile,
        )
        self.server = uvicorn.Server(config)
        self.running = True
        await self.server.serve()

    async def stop(self) -> None:
        """Stop the server."""
        if not self.running:
            logger.warning("Server is not running")
            return

        # Stop the server
        if self.server:
            self.server.should_exit = True
            await self.server.shutdown()
            self.server = None

        self.running = False


# Global server instance
_server: Optional[Server] = None


def get_server() -> Server:
    """Get the global server.

    Returns:
        The global server
    """
    global _server
    if _server is None:
        _server = Server()
    return _server


def set_server(server: Server) -> None:
    """Set the global server.

    Args:
        server: The server to use
    """
    global _server
    _server = server


def get_router() -> Router:
    """Get the global router.

    Returns:
        The global router
    """
    return get_server().router


def add_route(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    methods: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> None:
    """Add a route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        methods: The HTTP methods to route
        name: The name of the route
    """
    get_router().add_route(path, handler, methods, name)


def get(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add a GET route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().get(path, handler, name)


def post(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add a POST route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().post(path, handler, name)


def put(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add a PUT route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().put(path, handler, name)


def delete(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add a DELETE route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().delete(path, handler, name)


def patch(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add a PATCH route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().patch(path, handler, name)


def head(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add a HEAD route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().head(path, handler, name)


def options(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    name: Optional[str] = None,
) -> None:
    """Add an OPTIONS route to the global router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().options(path, handler, name)


async def start() -> None:
    """Start the global server."""
    await get_server().start()


async def stop() -> None:
    """Stop the global server."""
    await get_server().stop()


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
