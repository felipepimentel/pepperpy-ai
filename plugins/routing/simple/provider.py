"""
Simple routing provider for AI Gateway.

This provider implements basic HTTP routing for AI requests.
"""

import asyncio
import json
from typing import dict, list, set, Any

from pepperpy.routing import RoutingProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.routing.base import RoutingError
from pepperpy.routing.base import RoutingError

logger = logger.getLogger(__name__)


class SimpleRoutingProvider(class SimpleRoutingProvider(RoutingProvider, BasePluginProvider):
    """Simple HTTP routing provider for AI Gateway."""):
    """
    Routing simplerouting provider.
    
    This provider implements simplerouting functionality for the PepperPy routing framework.
    """

    async def initialize(self) -> None:
 """Initialize the provider.

        This method is called automatically when the provider is first used.
 """
        # Initialize state
        self.initialized = True

        # Get configuration
        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", 8080)

        # Initialize internal state
        self.running = False
        self.server = None
        self.backends: dict[str, Any] = {}
        self.auth_provider = None
        self.http_app = None
        self.shutdown_event = asyncio.Event()

        self.logger.info("Initializing simple routing provider")

        try:
            # Import required modules
            import aiohttp
            from aiohttp import web

            # Create HTTP app
            self.http_app = web.Application()

            # set up routes
            self.http_app.router.add_post(
                "/api/v1/{backend}/{operation}", self._handle_request
            )
            self.http_app.router.add_get("/health", self._handle_health)
            self.http_app.router.add_get("/", self._handle_root)

            self.logger.info("Simple routing provider initialized")

        except ImportError as e:
            self.logger.error(f"Failed to initialize routing provider: {e}")
            raise ImportError(f"Required package not found: {e}") from e

    async def cleanup(self) -> None:
 """Clean up provider resources.

        This method is called automatically when the context manager exits.
 """
        if not self.initialized:
            return

        self.logger.info("Cleaning up simple routing provider")

        # Stop the server if running
        if self.running:
            await self.stop()

        # Clean up backends
        for name, backend in list(self.backends.items()):
            try:
                # Attempt to clean up backend if it has a cleanup method
                if hasattr(backend, "cleanup"):
                    await backend.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up backend {name}: {e}")

        self.backends.clear()
        self.initialized = False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a routing operation.

        Args:
            input_data: Task data containing:
                - task: Task name (start, stop, configure, register_backend, unregister_backend, get_backends)
                - host: Host to bind to (for configure task)
                - port: Port to listen on (for configure task)
                - name: Backend name (for register/unregister tasks)
                - provider: Backend provider (for register task)
                - auth_provider: Auth provider instance

        Returns:
            Operation result
        """
        task = input_data.get("task")

        if not task:
            raise RoutingError("No task specified")

        try:
            if task == "configure":
                host = input_data.get("host")
                port = input_data.get("port")
                await self.configure(host, port)
                return {
                    "status": "success",
                    "message": f"Configured for {self.host}:{self.port}",
                }

            elif task == "start":
                await self.start()
                return {
                    "status": "success",
                    "message": f"Server started on {self.host}:{self.port}",
                }

            elif task == "stop":
                await self.stop()
                return {"status": "success", "message": "Server stopped"}

            elif task == "register_backend":
                name = input_data.get("name")
                provider = input_data.get("provider")

                if not name or not provider:
                    raise RoutingError("Name and provider are required",
                    )

                return await self.register_backend(name, provider)

            elif task == "unregister_backend":
                name = input_data.get("name")

                if not name:
                    raise RoutingError("Name is required")

                return await self.unregister_backend(name)

            elif task == "get_backends":
                backends = await self.get_backends()
                return {"status": "success", "backends": backends}

            elif task == "set_auth_provider":
                auth_provider = input_data.get("auth_provider")

                if not auth_provider:
                    raise RoutingError("Auth provider is required")

                self.auth_provider = auth_provider
                self.logger.info("Auth provider set")
                return {"status": "success", "message": "Auth provider set"}

            elif task == "status":
                backends = await self.get_backends()
                return {
                    "status": "success",
                    "running": self.running,
                    "host": self.host,
                    "port": self.port,
                    "backends": backends,
                    "has_auth_provider": self.auth_provider is not None,
                }

            else:
                raise RoutingError(f"Unknown task: {task)"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task}': {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_root(self, request):
        """Handle root endpoint requests."""
        from aiohttp import web

        backend_list = list(self.backends.keys())
        return web.json_response(
            {
                "status": "success",
                "service": "AI Gateway",
                "backends": backend_list,
            }
        )

    async def _handle_health(self, request):
        """Handle health check requests."""
        from aiohttp import web

        return web.json_response(
            {
                "status": "success",
                "service": "AI Gateway",
                "running": self.running,
            }
        )

    async def _handle_request(self, request):
        """Handle API requests."""
        from aiohttp import web

        # Extract path parameters
        backend_name = request.match_info.get("backend")
        operation = request.match_info.get("operation")

        # Check if backend exists
        if backend_name not in self.backends:
            return web.json_response(
                {"status": "error", "message": f"Backend not found: {backend_name}"},
                status=404,
            )

        # Get backend instance
        backend = self.backends[backend_name]

        # Authenticate request if auth provider is configured
        if self.auth_provider:
            # Convert request to a format the auth provider can process
            auth_request = {
                "headers": dict(request.headers),
                "method": request.method,
                "path": request.path,
            }

            auth_result = await self.auth_provider.authenticate(auth_request)
            if not auth_result.get("authenticated", False):
                # Authentication failed
                return web.json_response(
                    {
                        "status": "error",
                        "message": auth_result.get("error", "Authentication failed"),
                    },
                    status=401,
                )

            # Add auth info to request for backends that need it
            auth_info = auth_result.copy()

        # Process the request with the backend
        try:
            # Parse request body
            body = await request.json()

            # Call the backend with operation and request data
            if hasattr(backend, operation):
                method = getattr(backend, operation)
                result = await method(body)
            elif hasattr(backend, "execute"):
                # Fallback to generic execute method
                result = await backend.execute({"operation": operation, "data": body})
            else:
                return web.json_response(
                    {
                        "status": "error",
                        "message": f"Operation not supported: {operation}",
                    },
                    status=400,
                )

            # Return the result
            return web.json_response(result)

        except json.JSONDecodeError:
            return web.json_response(
                {"status": "error", "message": "Invalid JSON in request body"},
                status=400,
            )

        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return web.json_response(
                {"status": "error", "message": f"Error processing request: {e!s}"},
                status=500,
            )

    async def configure(self, host: str | None = None, port: int | None = None) -> None:
        """Configure the provider.

        Args:
            host: Server host
            port: Server port
        """
        if host:
            self.host = host
        if port:
            self.port = port

        self.logger.info(f"Configured routing provider for {self.host}:{self.port}")

    async def start(self) -> None:
 """Start the HTTP server.
 """
        if not self.initialized:
            await self.initialize()

        if self.running:
            self.logger.warning("Server is already running")
            return

        try:
            from aiohttp import web

            # Create a runner for the app
            runner = web.AppRunner(self.http_app)
            await runner.setup()

            # Create site and start it
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()

            # Store reference to server
            self.server = {"runner": runner, "site": site}
            self.running = True

            self.logger.info(f"Server started on {self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise RuntimeError(f"Failed to start server: {e}") from e

    async def stop(self) -> None:
 """Stop the HTTP server.
 """
        if not self.running or not self.server:
            self.logger.warning("Server is not running")
            return

        try:
            # Get runner from server dict
            runner = self.server.get("runner")
            if runner:
                await runner.cleanup()

            self.server = None
            self.running = False

            self.logger.info("Server stopped")

        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
            raise RuntimeError(f"Error stopping server: {e}") from e

    async def register_backend(self, name: str, provider: Any) -> dict[str, Any]:
        """Register a backend provider.

        Args:
            name: Backend name
            provider: Backend provider instance

        Returns:
            Registration result
        """
        if name in self.backends:
            raise RoutingError(f"Backend already registered: {name)"}

        # Register backend
        self.backends[name] = provider
        self.logger.info(f"Registered backend: {name}")

        return {
            "status": "success",
            "message": f"Backend registered: {name}",
            "backend": name,
        }

    async def unregister_backend(self, name: str) -> dict[str, Any]:
        """Unregister a backend provider.

        Args:
            name: Backend name

        Returns:
            Unregistration result
        """
        if name not in self.backends:
            raise RoutingError(f"Backend not found: {name)"}

        # Try to clean up backend if it has a cleanup method
        backend = self.backends[name]
        try:
            if hasattr(backend, "cleanup"):
                await backend.cleanup()
        except Exception as e:
            raise RoutingError(f"Operation failed: {e}") from e
            self.logger.warning(f"Error cleaning up backend {name}: {e}")

        # Unregister backend
        del self.backends[name]
        self.logger.info(f"Unregistered backend: {name}")

        return {"status": "success", "message": f"Backend unregistered: {name}"}

    async def get_backends(self) -> list[str]:
        """Get list of registered backends.

        Returns:
            list of backend names
        """
        return list(self.backends.keys())
