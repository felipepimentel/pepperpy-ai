"""Basic routing provider for AI Gateway."""

import json
import traceback
from collections.abc import Callable
from typing import Any

from aiohttp import web

from pepperpy.core.logging import get_logger
from pepperpy.plugin import PepperpyPlugin

logger = get_logger(__name__)


class BasicRoutingProvider(PepperpyPlugin):
    """Basic routing provider using aiohttp."""

    plugin_type = "routing"
    provider_name = "basic"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the routing provider.

        Args:
            **kwargs: Provider configuration
        """
        super().__init__()
        self.config = kwargs or {}
        self.host = self.config.get("host", "0.0.0.0")
        self.port = self.config.get("port", 8080)
        self.cors_origins = self.config.get("cors_origins", ["*"])
        self.log_requests = self.config.get("log_requests", True)

        self.initialized = False
        self.running = False
        self.app: web.Application | None = None  # Use Optional to handle None
        self.runner = None
        self.site = None
        self.auth_provider = None
        self.backends = {}
        self.server_task = None

    async def initialize(self) -> None:
        """Initialize the routing provider."""
        if self.initialized:
            return

        logger.info("Initializing Basic Routing Provider")

        # Create aiohttp application
        self.app = web.Application(middlewares=[self._auth_middleware])

        # Set up CORS
        if self.cors_origins:
            logger.info(f"Configuring CORS with origins: {self.cors_origins}")
            # Note: In a production app, you would add proper CORS middleware here

        # Set up routes
        self.app.router.add_get("/", self._handle_home)
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/providers", self._handle_providers)
        self.app.router.add_post("/api/{provider_id}", self._handle_api_request)

        self.initialized = True
        logger.info("Basic Routing Provider initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        logger.info("Cleaning up Basic Routing Provider")

        # Stop server if running
        if self.running:
            await self.stop()

        # Clear backends
        self.backends.clear()

        self.initialized = False
        logger.info("Basic Routing Provider cleaned up")

    async def configure(self, host: str, port: int) -> None:
        """Configure the routing provider.

        Args:
            host: The host to bind to
            port: The port to listen on
        """
        self.host = host
        self.port = port
        logger.info(f"Configured Basic Routing Provider for {host}:{port}")

    async def start(self) -> None:
        """Start the routing server."""
        if not self.initialized:
            await self.initialize()

        if self.running:
            logger.warning("Routing server is already running")
            return

        logger.info(f"Starting routing server on {self.host}:{self.port}")

        # Create and start the runner
        if self.app is None:  # Add a safety check
            logger.error("Application is not initialized")
            return

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        self.running = True
        logger.info(f"Routing server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the routing server."""
        if not self.running:
            logger.warning("Routing server is not running")
            return

        logger.info("Stopping routing server")

        if self.site:
            await self.site.stop()

        if self.runner:
            await self.runner.cleanup()

        self.running = False
        self.site = None
        self.runner = None
        logger.info("Routing server stopped")

    async def register_backend(self, name: str, provider: Any) -> dict[str, Any]:
        """Register an AI backend provider.

        Args:
            name: The backend name/ID
            provider: The backend provider instance

        Returns:
            Registration result
        """
        if name in self.backends:
            return {"status": "error", "message": f"Backend {name} already registered"}

        self.backends[name] = provider
        logger.info(f"Registered backend provider: {name}")

        return {
            "status": "success",
            "message": f"Backend {name} registered successfully",
            "provider": name,
        }

    async def unregister_backend(self, name: str) -> dict[str, Any]:
        """Unregister an AI backend provider.

        Args:
            name: The backend name/ID

        Returns:
            Unregistration result
        """
        if name not in self.backends:
            return {"status": "error", "message": f"Backend {name} not registered"}

        del self.backends[name]
        logger.info(f"Unregistered backend provider: {name}")

        return {
            "status": "success",
            "message": f"Backend {name} unregistered successfully",
            "provider": name,
        }

    async def set_auth_provider(self, auth_provider: Any) -> None:
        """Set the authentication provider.

        Args:
            auth_provider: The authentication provider instance
        """
        self.auth_provider = auth_provider
        logger.info("Auth provider set")

    @web.middleware
    async def _auth_middleware(
        self, request: web.Request, handler: Callable
    ) -> web.Response:
        """Authentication middleware.

        Args:
            request: The HTTP request
            handler: The route handler

        Returns:
            The HTTP response
        """
        # Skip auth for certain paths
        if request.path in ["/", "/health"]:
            return await handler(request)

        # Perform authentication if provider is available
        if self.auth_provider:
            # Extract headers as dict
            headers = {key: value for key, value in request.headers.items()}

            # Authenticate request
            auth_result = await self.auth_provider.authenticate(headers)

            if not auth_result.get("authenticated", False):
                error = auth_result.get("error", "Authentication failed")
                return web.json_response(
                    {"status": "error", "message": error}, status=401
                )

            # Set authenticated user in request
            request["user_id"] = auth_result.get("user_id")

        # Process the request
        try:
            return await handler(request)
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            logger.error(traceback.format_exc())
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def _handle_home(self, request: web.Request) -> web.Response:
        """Handle home route.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        return web.json_response({
            "status": "success",
            "message": "AI Gateway is running",
            "backends": list(self.backends.keys()),
        })

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check route.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        return web.json_response({
            "status": "success",
            "healthy": True,
        })

    async def _handle_providers(self, request: web.Request) -> web.Response:
        """Handle providers list route.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        return web.json_response({
            "status": "success",
            "providers": list(self.backends.keys()),
        })

    async def _handle_api_request(self, request: web.Request) -> web.Response:
        """Handle API request route.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        provider_id = request.match_info.get("provider_id")

        if not provider_id:
            return web.json_response(
                {"status": "error", "message": "No provider specified"}, status=400
            )

        if provider_id not in self.backends:
            return web.json_response(
                {"status": "error", "message": f"Provider {provider_id} not found"},
                status=404,
            )

        # Get the provider
        provider = self.backends[provider_id]

        # Parse request data
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )

        # Add authenticated user if available
        if "user_id" in request:
            data["user_id"] = request["user_id"]

        # Log request if enabled
        if self.log_requests:
            logger.info(f"API Request: {provider_id} - {data}")

        # Process request
        try:
            result = await provider.execute(data)
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            logger.error(traceback.format_exc())
            return web.json_response({"status": "error", "message": str(e)}, status=500)
