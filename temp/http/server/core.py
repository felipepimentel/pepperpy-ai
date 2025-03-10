"""Core functionality for HTTP server.

This module provides the core functionality for HTTP server,
including request handling, routing, and middleware.
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
    """Base class for HTTP handlers.

    HTTP handlers are responsible for handling HTTP requests and returning responses.
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
    """Base class for JSON HTTP handlers.

    JSON HTTP handlers are responsible for handling HTTP requests and returning JSON responses.
    """

    @abstractmethod
    async def handle_json(self, request: Request) -> Dict[str, Any]:
        """Handle an HTTP request and return a JSON response.

        Args:
            request: The HTTP request to handle

        Returns:
            The JSON response

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
            logger.exception("Error handling request")
            raise HandlerError(f"Error handling request: {e}") from e


class FunctionHandler(Handler):
    """Handler that wraps a function.

    This handler wraps a function that takes a request and returns a response.
    """

    def __init__(self, func: Callable[[Request], Response]):
        """Initialize a function handler.

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
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(request)
            else:
                return self.func(request)
        except Exception as e:
            logger.exception("Error handling request")
            raise HandlerError(f"Error handling request: {e}") from e


class Router:
    """HTTP router.

    HTTP routers are responsible for routing HTTP requests to handlers.
    """

    def __init__(self):
        """Initialize a router."""
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
        if isinstance(handler, Handler):
            endpoint = handler.handle
        else:
            endpoint = FunctionHandler(handler).handle

        self.routes.append(
            Route(
                path=path,
                endpoint=endpoint,
                methods=methods,
                name=name,
            )
        )

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

    HTTP servers are responsible for serving HTTP requests.
    """

    def __init__(
        self,
        router: Optional[Router] = None,
        options: Optional[ServerOptions] = None,
    ):
        """Initialize a server.

        Args:
            router: The router to use
            options: Options for the server
        """
        self.router = router or Router()
        self.options = options or ServerOptions()
        self.app = None

    def build_app(self) -> Starlette:
        """Build the Starlette application.

        Returns:
            The Starlette application
        """
        app = Starlette(
            debug=self.options.debug,
            routes=self.router.routes,
            middleware=self.options.middleware,
        )

        return app

    async def start(self) -> None:
        """Start the server.

        Raises:
            RuntimeError: If the server is already running
        """
        if self.app is not None:
            raise RuntimeError("Server is already running")

        self.app = self.build_app()

        import uvicorn

        config = uvicorn.Config(
            app=self.app,
            host=self.options.host,
            port=self.options.port,
            log_level=logging.getLevelName(self.options.log_level).lower(),
            ssl_certfile=self.options.ssl_certfile,
            ssl_keyfile=self.options.ssl_keyfile,
        )

        server = uvicorn.Server(config)
        await server.serve()

    async def stop(self) -> None:
        """Stop the server.

        Raises:
            RuntimeError: If the server is not running
        """
        if self.app is None:
            raise RuntimeError("Server is not running")

        self.app = None


# Default server
_server = Server()


def get_server() -> Server:
    """Get the default server.

    Returns:
        The default server
    """
    return _server


def set_server(server: Server) -> None:
    """Set the default server.

    Args:
        server: The server to set as the default
    """
    global _server
    _server = server


def get_router() -> Router:
    """Get the default router.

    Returns:
        The default router
    """
    return get_server().router


def add_route(
    path: str,
    handler: Union[Handler, Callable[[Request], Response]],
    methods: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> None:
    """Add a route to the default router.

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
    """Add a GET route to the default router.

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
    """Add a POST route to the default router.

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
    """Add a PUT route to the default router.

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
    """Add a DELETE route to the default router.

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
    """Add a PATCH route to the default router.

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
    """Add a HEAD route to the default router.

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
    """Add an OPTIONS route to the default router.

    Args:
        path: The path to route
        handler: The handler to route to
        name: The name of the route
    """
    get_router().options(path, handler, name)


async def start() -> None:
    """Start the default server.

    Raises:
        RuntimeError: If the server is already running
    """
    await get_server().start()


async def stop() -> None:
    """Stop the default server.

    Raises:
        RuntimeError: If the server is not running
    """
    await get_server().stop()
