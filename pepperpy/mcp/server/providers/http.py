"""
HTTP server provider for MCP.

This module provides an HTTP server implementation for the MCP protocol.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

from aiohttp import web

from pepperpy.core.logging import get_logger
from pepperpy.mcp.protocol import MCPRequest, MCPResponse
from pepperpy.mcp.server.base import MCPServerProvider

logger = get_logger(__name__)


class HTTPServerProvider(MCPServerProvider):
    """HTTP server implementation for MCP."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with configuration."""
        super().__init__(**kwargs)
        self.app: web.Application | None = None
        self.runner: web.AppRunner | None = None
        self.site: web.TCPSite | None = None
        self.cors_origins = self.config.get("cors_origins", ["*"])
        self.auth_token = self.config.get("auth_token", "")

    async def initialize(self) -> None:
        """Initialize the provider."""
        if self.initialized:
            return

        logger.info("Initializing HTTP MCP server")

        # Create the aiohttp application
        self.app = web.Application()

        # Add CORS middleware if needed
        if self.cors_origins:
            import aiohttp_cors

            cors = aiohttp_cors.setup(
                self.app,
                defaults={
                    origin: aiohttp_cors.ResourceOptions(
                        allow_credentials=True,
                        expose_headers="*",
                        allow_headers="*",
                        allow_methods=["GET", "POST", "OPTIONS"],
                    )
                    for origin in self.cors_origins
                },
            )

        # Set up routes
        self.app.add_routes([
            web.get("/health", self._handle_health),
            web.get("/models", self._handle_models),
            web.post("/api/v1/request", self._handle_request),
            web.post("/api/v1/stream", self._handle_stream),
        ])

        # Apply CORS to routes if configured
        if self.cors_origins:
            for route in list(self.app.router.routes()):
                cors.add(route)

        self.initialized = True

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        logger.info("Cleaning up HTTP MCP server")

        if self.site:
            await self.site.stop()
            self.site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        self.app = None
        self.initialized = False
        self.running = False

    async def start(self, host: str | None = None, port: int | None = None) -> None:
        """Start the MCP server."""
        await super().start(host, port)

        if not self.initialized:
            await self.initialize()

        if not self.app:
            raise RuntimeError("HTTP server not initialized")

        if self.running:
            logger.warning("HTTP server is already running")
            return

        logger.info(f"Starting HTTP MCP server on {self.host}:{self.port}")

        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            self.running = True
            logger.info(f"HTTP MCP server running on http://{self.host}:{self.port}")
        except Exception as e:
            logger.exception(f"Error starting HTTP server: {e}")
            self.running = False
            raise RuntimeError(f"Failed to start HTTP server: {e}")

    async def stop(self) -> None:
        """Stop the MCP server."""
        await super().stop()

        if not self.running:
            logger.warning("HTTP server is not running")
            return

        logger.info("Stopping HTTP MCP server")

        if self.site:
            await self.site.stop()
            self.site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        self.running = False
        logger.info("HTTP MCP server stopped")

    async def register_model(self, model_id: str, model: Any) -> None:
        """Register a model with the server."""
        await super().register_model(model_id, model)

    async def unregister_model(self, model_id: str) -> None:
        """Unregister a model from the server."""
        await super().unregister_model(model_id)

    async def register_handler(
        self, operation: str, handler: Any, is_stream: bool = False
    ) -> None:
        """Register a custom handler for an operation."""
        await super().register_handler(operation, handler, is_stream)

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle a request."""
        return await super().handle_request(request)

    async def handle_stream_request(
        self, request: MCPRequest
    ) -> AsyncGenerator[MCPResponse, None]:
        """Handle a streaming request."""
        async for response in super().handle_stream_request(request):
            yield response

    # HTTP handlers
    async def _handle_health(self, request: web.Request) -> web.Response:
        """Handle health check requests."""
        if not self._authenticate(request):
            return web.Response(
                status=401,
                text=json.dumps({"error": "Unauthorized"}),
                content_type="application/json",
            )

        return web.Response(
            text=json.dumps({
                "status": "healthy",
                "running": self.running,
                "models": len(self._models),
            }),
            content_type="application/json",
        )

    async def _handle_models(self, request: web.Request) -> web.Response:
        """Handle model listing requests."""
        if not self._authenticate(request):
            return web.Response(
                status=401,
                text=json.dumps({"error": "Unauthorized"}),
                content_type="application/json",
            )

        models = await self.get_models()
        return web.Response(text=json.dumps(models), content_type="application/json")

    async def _handle_request(self, request: web.Request) -> web.Response:
        """Handle API requests."""
        if not self._authenticate(request):
            return web.Response(
                status=401,
                text=json.dumps({"error": "Unauthorized"}),
                content_type="application/json",
            )

        try:
            # Parse the request JSON
            data = await request.json()

            # Convert to MCPRequest
            mcp_request = MCPRequest.from_dict(data)

            # Handle the request
            mcp_response = await self.handle_request(mcp_request)

            # Return the response
            return web.Response(
                text=json.dumps(mcp_response.to_dict()), content_type="application/json"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON request: {e}")
            return web.Response(
                status=400,
                text=json.dumps({"error": f"Invalid JSON: {e!s}"}),
                content_type="application/json",
            )
        except Exception as e:
            logger.exception(f"Error handling request: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": f"Server error: {e!s}"}),
                content_type="application/json",
            )

    async def _handle_stream(self, request: web.Request) -> web.StreamResponse:
        """Handle streaming API requests."""
        if not self._authenticate(request):
            return web.Response(
                status=401,
                text=json.dumps({"error": "Unauthorized"}),
                content_type="application/json",
            )

        try:
            # Parse the request JSON
            data = await request.json()

            # Convert to MCPRequest
            mcp_request = MCPRequest.from_dict(data)

            # Set up streaming response
            response = web.StreamResponse(
                status=200,
                reason="OK",
                headers={"Content-Type": "application/x-ndjson"},
            )
            await response.prepare(request)

            # Handle the stream request
            async for chunk in self.handle_stream_request(mcp_request):
                # Convert the response to JSON and send
                chunk_json = json.dumps(chunk.to_dict()) + "\n"
                await response.write(chunk_json.encode())
                await response.drain()

            # End the response
            await response.write_eof()
            return response

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON request: {e}")
            return web.Response(
                status=400,
                text=json.dumps({"error": f"Invalid JSON: {e!s}"}),
                content_type="application/json",
            )
        except Exception as e:
            logger.exception(f"Error handling stream request: {e}")
            return web.Response(
                status=500,
                text=json.dumps({"error": f"Server error: {e!s}"}),
                content_type="application/json",
            )

    # Helper methods
    def _authenticate(self, request: web.Request) -> bool:
        """Authenticate a request.

        Args:
            request: The HTTP request

        Returns:
            True if the request is authenticated, False otherwise
        """
        # If no auth token is configured, allow all requests
        if not self.auth_token:
            return True

        # Check the Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return token == self.auth_token

        # Check the token query parameter
        token = request.query.get("token", "")
        return token == self.auth_token
