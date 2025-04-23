"""Basic routing provider for AI Gateway."""

import traceback
from collections.abc import Callable
import collections.abc
from typing import dict, set, Any

from aiohttp import web

from pepperpy.routing import RoutingProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.routing.base import RoutingError
from pepperpy.routing.base import RoutingError

logger = logger.getLogger(__name__)


class BasicRoutingProvider(class BasicRoutingProvider(RoutingProvider, BasePluginProvider):
    """Basic routing provider using aiohttp."""):
    """
    Routing basicrouting provider.
    
    This provider implements basicrouting functionality for the PepperPy routing framework.
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
        self.cors_origins = self.config.get("cors_origins", ["*"])
        self.log_requests = self.config.get("log_requests", True)

        self.running = False
        self.auth_provider = None
        self.backends = {}
        self.server_task = None
        self.runner = None
        self.site = None

        self.logger.info("Initializing Basic Routing Provider")

        # Create aiohttp application
        self.app = web.Application(middlewares=[self._auth_middleware])

        # set up CORS
        if self.cors_origins:
            self.logger.info(f"Configuring CORS with origins: {self.cors_origins}")
            # Note: In a production app, you would add proper CORS middleware here

        # set up routes
        self.app.router.add_get("/", self._handle_home)
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/providers", self._handle_providers)
        self.app.router.add_post("/api/{provider_id}", self._handle_api_request)

        self.logger.info("Basic Routing Provider initialized")

    async def cleanup(self) -> None:
 """Clean up resources.

        This method is called automatically when the context manager exits.
 """
        if not self.initialized:
            return

        self.logger.info("Cleaning up Basic Routing Provider")

        # Stop server if running
        if self.running:
            await self.stop()

        # Clear backends
        self.backends.clear()

        self.initialized = False
        self.logger.info("Basic Routing Provider cleaned up")

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute a routing operation.

        Args:
            input_data: Task data containing:
                - task: Task name (start, stop, register_backend, unregister_backend, set_auth_provider)
                - host: Host to bind to (for configure task)
                - port: Port to listen on (for configure task)
                - name: Backend name (for register/unregister tasks)
                - provider: Backend provider (for register task)
                - auth_provider: Auth provider (for set_auth_provider task)

        Returns:
            Operation result
        """
        task = input_data.get("task")

        if not task:
            raise RoutingError("No task specified")

        try:
            if task == "configure":
                host = input_data.get("host", self.host)
                port = input_data.get("port", self.port)

                await self.configure(host, port)
                return {"status": "success", "message": f"Configured for {host}:{port}"}

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

            elif task == "set_auth_provider":
                auth_provider = input_data.get("auth_provider")

                if not auth_provider:
                    raise RoutingError("Auth provider is required")

                await self.set_auth_provider(auth_provider)
                return {"status": "success", "message": "Auth provider set"}

            elif task == "status":
                return {
                    "status": "success",
                    "running": self.running,
                    "host": self.host,
                    "port": self.port,
                    "backends": list(self.backends.keys()),
                    "has_auth_provider": self.auth_provider is not None,
                }

            else:
                raise RoutingError(f"Unknown task: {task)"}

        except Exception as e:
            self.logger.error(f"Error executing task '{task}': {e}")
            self.logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    async def configure(self, host: str, port: int) -> None:
        """Configure the routing provider.

        Args:
            host: The host to bind to
            port: The port to listen on
        """
        self.host = host
        self.port = port
        self.logger.info(f"Configured Basic Routing Provider for {host}:{port}")

    async def start(self) -> None:
 """Start the routing server.
 """
        if not self.initialized:
            await self.initialize()

        if self.running:
            self.logger.warning("Routing server is already running")
            return

        self.logger.info(f"Starting routing server on {self.host}:{self.port}")

        # Create and start the runner
        if self.app is None:  # Add a safety check
            self.logger.error("Application is not initialized")
            return

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        self.running = True
        self.logger.info(f"Routing server started on {self.host}:{self.port}")

    async def stop(self) -> None:
 """Stop the routing server.
 """
        if not self.running:
            self.logger.warning("Routing server is not running")
            return

        self.logger.info("Stopping routing server")

        if self.site:
            await self.site.stop()

        if self.runner:
            await self.runner.cleanup()

        self.running = False
        self.site = None
        self.runner = None
        self.logger.info("Routing server stopped")

    async def register_backend(self, name: str, provider: Any) -> dict[str, Any]:
        """Register an AI backend provider.

        Args:
            name: The backend name/ID
            provider: The backend provider instance

        Returns:
            Registration result
        """
        if name in self.backends:
            raise RoutingError(f"Backend {name) already registered"}

        self.backends[name] = provider
        self.logger.info(f"Registered backend provider: {name}")

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
            raise RoutingError(f"Backend {name) not registered"}

        del self.backends[name]
        self.logger.info(f"Unregistered backend provider: {name}")

        return {
            "status": "success",
            "message": f"Backend {name} unregistered successfully",
            "provider": name,
        }

    async def set_auth_provider(self, auth_provider: Any) -> None:
        """set the authentication provider.

        Args:
            auth_provider: The authentication provider instance
        """
        self.auth_provider = auth_provider
        self.logger.info("Auth provider set")

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
        # Skip authentication for non-API routes
        if not request.path.startswith("/api/"):
            return await handler(request)

        # Skip authentication if no auth provider is set
        if not self.auth_provider:
            self.logger.warning("No auth provider set, skipping authentication")
            return await handler(request)

        try:
            # Authenticate the request
            result = await self.auth_provider.authenticate(dict(request.headers))

            if not result.get("authenticated", False):
                error_msg = result.get("error", "Authentication failed")
                self.logger.warning(f"Authentication failed: {error_msg}")
                return web.json_response(
                    {"error": error_msg, "authenticated": False}, status=401
                )

            # set user_id in request
            request["user_id"] = result.get("user_id", "anonymous")
            self.logger.debug(f"Authenticated user: {request['user_id']}")

            return await handler(request)
        except Exception as e:
            raise RoutingError(f"Operation failed: {e}") from e
            self.logger.error(f"Authentication error: {e}")
            return web.json_response(
                {"error": "Authentication error", "authenticated": False}, status=500
            )

    async def _handle_home(self, request: web.Request) -> web.Response:
        """Handle requests to the home route.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        if self.log_requests:
            self.logger.info(f"GET / from {request.remote}")

        return web.json_response(
            {
                "name": "PepperPy AI Gateway",
                "version": "0.1.0",
                "status": "ok",
            }
        )

    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle requests to the health route.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        if self.log_requests:
            self.logger.info(f"GET /health from {request.remote}")

        return web.json_response({"status": "ok"})

    async def _handle_providers(self, request: web.Request) -> web.Response:
        """Handle requests to list providers.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        if self.log_requests:
            self.logger.info(f"GET /providers from {request.remote}")

        providers = list(self.backends.keys())
        return web.json_response({"providers": providers})

    async def _handle_api_request(self, request: web.Request) -> web.Response:
        """Handle API requests.

        Args:
            request: The HTTP request

        Returns:
            The HTTP response
        """
        provider_id = request.match_info.get("provider_id")
        if self.log_requests:
            self.logger.info(f"POST /api/{provider_id} from {request.remote}")

        # Check if provider exists
        if provider_id not in self.backends:
            return web.json_response(
                {"error": f"Provider '{provider_id}' not found"}, status=404
            )

        try:
            # Get provider
            provider = self.backends[provider_id]

            # Parse request body
            body = await request.json()

            # Add user_id if authenticated
            if "user_id" in request:
                body["user_id"] = request["user_id"]

            # Process request
            response = await provider.process(body)

            return web.json_response(response)
        except Exception as e:
            raise RoutingError(f"Operation failed: {e}") from e
            self.logger.error(f"Error processing request: {e}")
            self.logger.error(traceback.format_exc())
            return web.json_response(
                {"error": f"Error processing request: {e!s}"}, status=500
            )
