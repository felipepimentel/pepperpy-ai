#!/usr/bin/env python3
"""
AI Gateway Portal Controller

This script runs both a web portal and the AI Gateway API on different ports.
- Portal Web UI: Port 8080
- API Gateway: Port 8081
"""

import argparse
import asyncio
import logging
import os
import sys

# Add the project root to sys.path if needed
if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "..")):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from plugins.workflow.ai_gateway.config import load_config, setup_logging
from plugins.workflow.ai_gateway.gateway import (
    AIGateway,
    create_auth_provider,
    create_routing_provider,
)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("portal_controller")


class PortalServer:
    """Simple web portal server for the AI Gateway."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        """Initialize the portal server.

        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.logger = logging.getLogger("portal_server")

    async def start(self):
        """Start the portal server."""
        from aiohttp import web

        app = web.Application()
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/status", self._handle_status)

        self.runner = web.AppRunner(app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        self.logger.info(f"Portal server started on http://{self.host}:{self.port}")

    async def stop(self):
        """Stop the portal server."""
        await self.runner.cleanup()
        self.logger.info("Portal server stopped")

    async def _handle_index(self, request):
        """Handle requests to the index page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Gateway Portal</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1 {
                    color: #333;
                }
                .card {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                }
                .endpoint {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 3px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <h1>AI Gateway Portal</h1>
            <div class="card">
                <h2>Gateway Status</h2>
                <p>The AI Gateway is running at: <span class="endpoint">http://localhost:8081/api</span></p>
                <p><a href="/status">View detailed status</a></p>
            </div>
            <div class="card">
                <h2>Available Endpoints</h2>
                <ul>
                    <li><span class="endpoint">http://localhost:8081/api/llm</span> - Language model API</li>
                    <li><span class="endpoint">http://localhost:8081/api/calculator</span> - Calculator tool</li>
                    <li><span class="endpoint">http://localhost:8081/api/weather</span> - Weather tool</li>
                </ul>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    async def _handle_status(self, request):
        """Handle requests to the status page."""
        status = {
            "portal": {
                "status": "running",
                "address": f"http://{self.host}:{self.port}",
            },
            "gateway": {"status": "running", "address": f"http://{self.host}:8081/api"},
        }
        return web.json_response(status)


async def run_gateway(
    config_path: str | None = None,
    host: str = "0.0.0.0",
    port: int = 8081,
    debug: bool = False,
) -> None:
    """Run the AI Gateway.

    Args:
        config_path: Path to configuration file
        host: Host address to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    logger = logging.getLogger("gateway")

    try:
        # Load configuration
        config = load_config(config_path)

        # Set up logging
        if debug:
            config.setdefault("logging", {})["level"] = "debug"
        setup_logging(config)

        # Override port in routing configuration
        routing_config = config.get("routing", {}).copy()
        routing_config["host"] = host
        routing_config["port"] = port
        config["routing"] = routing_config

        # Create auth provider
        auth_config = config.get("auth", {})
        auth_provider = await create_auth_provider(
            auth_config.get("provider", "basic"), **auth_config
        )
        await auth_provider.initialize()

        # Create routing provider
        routing_provider = await create_routing_provider(
            routing_config.get("provider", "basic"), **routing_config
        )
        await routing_provider.initialize()

        # Connect auth provider to routing provider
        await routing_provider.set_auth_provider(auth_provider)

        # Create gateway
        gateway = AIGateway()
        await gateway.initialize()
        await gateway.set_auth_provider(auth_provider)
        await gateway.set_routing_provider(routing_provider)

        # Start gateway - we need to check the actual gateway.start() signature
        logger.info(f"Starting AI Gateway on {host}:{port}")
        # Pass host and port to the gateway.start() method
        await gateway.start(host, port)

        # Wait for termination signal
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        logger.info("Gateway shutting down...")
        await gateway.stop()
        await routing_provider.cleanup()
        await auth_provider.cleanup()
    except Exception as e:
        logger.error(f"Error running gateway: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def run_portal_and_gateway(
    config_path: str | None = None,
    portal_port: int = 8080,
    api_port: int = 8081,
    debug: bool = False,
) -> None:
    """Run both the portal and gateway servers.

    Args:
        config_path: Path to configuration file
        portal_port: Port for the portal server
        api_port: Port for the API gateway
        debug: Enable debug mode
    """
    logger.info(
        f"Starting Portal on port {portal_port} and API Gateway on port {api_port}"
    )

    # Create portal server
    portal = PortalServer(port=portal_port)
    await portal.start()

    # Start gateway in a separate task
    gateway_task = asyncio.create_task(
        run_gateway(config_path, "0.0.0.0", api_port, debug)
    )

    try:
        # Wait for gateway task (it won't complete without cancellation)
        await gateway_task
    except asyncio.CancelledError:
        logger.info("Shutting down all servers...")
        # Cancel gateway task
        gateway_task.cancel()
        try:
            await gateway_task
        except asyncio.CancelledError:
            pass
        # Stop portal
        await portal.stop()
        logger.info("All servers stopped")


def main() -> int:
    """Command-line entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run AI Gateway Portal and API")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--portal-port", type=int, default=8080, help="Portal UI port (default: 8080)"
    )
    parser.add_argument(
        "--api-port", type=int, default=8081, help="API Gateway port (default: 8081)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    try:
        asyncio.run(
            run_portal_and_gateway(
                args.config, args.portal_port, args.api_port, args.debug
            )
        )
        return 0
    except KeyboardInterrupt:
        print("Servers stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
