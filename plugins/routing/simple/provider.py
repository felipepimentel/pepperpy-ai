"""
Simple routing provider for AI Gateway.

This provider implements basic HTTP routing for AI requests.
"""

import asyncio
import json
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin


class SimpleRoutingProvider(PepperpyPlugin):
    """Simple HTTP routing provider for AI Gateway."""

    plugin_type = "routing"
    provider_name = "simple"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the routing provider with configuration.

        Args:
            **kwargs: Configuration parameters
        """
        super().__init__()
        self.logger = get_logger("routing.simple")
        self.config = kwargs
        self.initialized = False
        self.running = False
        self.server = None
        self.host = "0.0.0.0"
        self.port = 8080
        self.backends: dict[str, Any] = {}
        self.auth_provider = None
        self.http_app = None
        self.shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize resources."""
        if self.initialized:
            return

        self.logger.info("Initializing simple routing provider")

        try:
            # Import required modules
            import aiohttp
            from aiohttp import web

            # Create HTTP app
            self.http_app = web.Application()

            # Set up routes
            self.http_app.router.add_post(
                "/api/v1/{backend}/{operation}", self._handle_request
            )
            self.http_app.router.add_get("/health", self._handle_health)
            self.http_app.router.add_get("/", self._handle_root)

            self.initialized = True
            self.logger.info("Simple routing provider initialized")

        except ImportError as e:
            self.logger.error(f"Failed to initialize routing provider: {e}")
            raise ImportError(f"Required package not found: {e}") from e

    async def _handle_root(self, request):
        """Handle root endpoint requests."""
        from aiohttp import web

        backend_list = list(self.backends.keys())
        return web.json_response({
            "status": "success",
            "service": "AI Gateway",
            "backends": backend_list,
        })

    async def _handle_health(self, request):
        """Handle health check requests."""
        from aiohttp import web

        return web.json_response({
            "status": "success",
            "service": "AI Gateway",
            "running": self.running,
        })

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

    async def cleanup(self) -> None:
        """Clean up resources."""
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

    async def configure(
        self, host: str | None = None, port: int | None = None, **kwargs: Any
    ) -> None:
        """Configure the provider.

        Args:
            host: Server host
            port: Server port
            **kwargs: Additional configuration parameters
        """
        self.logger.info("Configuring simple routing provider")

        if host:
            self.host = host
        if port:
            self.port = port

        # Store the auth provider if it's provided
        if "auth_provider" in kwargs:
            self.auth_provider = kwargs["auth_provider"]
            self.logger.info(
                f"Using auth provider: {type(self.auth_provider).__name__}"
            )

    async def start(self) -> None:
        """Start the routing server."""
        if not self.initialized:
            await self.initialize()

        if self.running:
            self.logger.warning("Server is already running")
            return

        try:
            from aiohttp import web

            # Ensure http_app is initialized
            if not self.http_app:
                self.logger.error("HTTP app not initialized")
                raise RuntimeError("HTTP app not initialized")

            # Create a runner for the app
            runner = web.AppRunner(self.http_app)
            await runner.setup()

            # Create a site
            site = web.TCPSite(runner, self.host, self.port)

            # Start the site
            await site.start()

            # Store references
            self.server = {
                "runner": runner,
                "site": site,
            }

            self.running = True
            self.logger.info(f"Server started on http://{self.host}:{self.port}")

            # Reset shutdown event
            self.shutdown_event.clear()

        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the routing server."""
        if not self.running or not self.server:
            self.logger.warning("Server is not running")
            return

        try:
            # Get the runner
            runner = self.server.get("runner")

            # Clean up the runner
            if runner:
                await runner.cleanup()

            self.server = None
            self.running = False

            # Set shutdown event
            self.shutdown_event.set()

            self.logger.info("Server stopped")

        except Exception as e:
            self.logger.error(f"Error stopping server: {e}")
            raise

    async def register_backend(self, name: str, provider: Any) -> dict[str, Any]:
        """Register a backend provider.

        Args:
            name: Backend name
            provider: Backend provider instance

        Returns:
            Registration result
        """
        if name in self.backends:
            self.logger.warning(f"Backend already registered: {name}")
            return {"status": "error", "message": f"Backend already registered: {name}"}

        # Store the backend
        self.backends[name] = provider
        self.logger.info(f"Registered backend: {name}")

        return {"status": "success", "backend": name}

    async def unregister_backend(self, name: str) -> dict[str, Any]:
        """Unregister a backend provider.

        Args:
            name: Backend name

        Returns:
            Unregistration result
        """
        if name not in self.backends:
            return {"status": "error", "message": f"Backend not found: {name}"}

        # Remove the backend
        backend = self.backends.pop(name)

        # Clean up backend resources if it has a cleanup method
        if hasattr(backend, "cleanup"):
            try:
                await backend.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up backend {name}: {e}")

        self.logger.info(f"Unregistered backend: {name}")

        return {"status": "success", "backend": name}

    async def get_backends(self) -> list[str]:
        """Get list of registered backends.

        Returns:
            List of backend names
        """
        return list(self.backends.keys())
