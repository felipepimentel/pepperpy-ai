#!/usr/bin/env python3
"""
Enhanced AI Gateway Portal

Production-ready implementation with:
- Multiple port support
- Health monitoring
- Metrics collection
- Rate limiting
- Environment variable configuration
"""

import argparse
import asyncio
import logging
import os
import sys
import time
import uuid

# Add the project root to sys.path if needed
if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "..")):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from plugins.workflow.ai_gateway.config import load_config, setup_logging
from plugins.workflow.ai_gateway.gateway import (
    AIGateway,
    create_auth_provider,
    create_routing_provider,
)

try:
    import aiohttp
    import aiohttp_cors
    from aiohttp import web
    from prometheus_client import Counter, Histogram, generate_latest
except ImportError:
    print("Required packages not installed. Installing dependencies...")
    import subprocess

    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "aiohttp",
        "aiohttp_cors",
        "prometheus_client",
    ])
    import aiohttp_cors
    from aiohttp import web
    from prometheus_client import Counter, Histogram, generate_latest

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("enhanced_portal")

# Metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "port", "status"],
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint", "port"],
)

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total", "Total rate limit hits", ["endpoint", "ip"]
)

# Default rate limits (requests per minute)
DEFAULT_RATE_LIMITS = {
    "/api/llm": 60,  # 1 request per second
    "/api/calculator": 300,  # 5 requests per second
    "/api/weather": 60,  # 1 request per second
}


class RateLimiter:
    """Simple rate limiter using sliding window."""

    def __init__(self, limit_map: dict[str, int] = None):
        """Initialize rate limiter.

        Args:
            limit_map: Map of endpoint prefixes to requests per minute limits
        """
        self.limit_map = limit_map or DEFAULT_RATE_LIMITS
        self._request_records: dict[str, list[float]] = {}
        self._cleanup_interval = 60  # Cleanup every minute
        self._last_cleanup = time.time()

    def is_rate_limited(self, ip: str, path: str) -> bool:
        """Check if a request should be rate limited.

        Args:
            ip: Client IP address
            path: Request path

        Returns:
            True if request should be rate limited
        """
        now = time.time()

        # Clean up old records periodically
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_old_records(now)
            self._last_cleanup = now

        # Find matching limit
        limit = None
        for prefix, rate in self.limit_map.items():
            if path.startswith(prefix):
                limit = rate
                break

        if limit is None:
            return False  # No rate limit for this path

        # Get or create record for this IP + path
        key = f"{ip}:{path.split('?')[0]}"  # Remove query parameters
        if key not in self._request_records:
            self._request_records[key] = []

        # Remove records older than 1 minute
        minute_ago = now - 60
        self._request_records[key] = [
            t for t in self._request_records[key] if t > minute_ago
        ]

        # Check if we're over the limit
        if len(self._request_records[key]) >= limit:
            RATE_LIMIT_HITS.labels(endpoint=path, ip=ip).inc()
            return True

        # Add this request
        self._request_records[key].append(now)
        return False

    def _cleanup_old_records(self, now: float) -> None:
        """Clean up old records."""
        minute_ago = now - 60
        for key in list(self._request_records.keys()):
            self._request_records[key] = [
                t for t in self._request_records[key] if t > minute_ago
            ]
            if not self._request_records[key]:
                del self._request_records[key]


class MetricsMiddleware:
    """Middleware to collect metrics for requests."""

    async def middleware(self, app, handler):
        """Process a request and record metrics."""

        async def middleware_handler(request):
            # Generate request ID for tracking
            request_id = str(uuid.uuid4())
            request["request_id"] = request_id

            # Get port from request
            port = request.transport.get_extra_info("sockname")[1]

            # Start timer for request latency
            start_time = time.time()

            try:
                # Process request
                response = await handler(request)

                # Record metrics
                HTTP_REQUESTS.labels(
                    method=request.method,
                    endpoint=request.path,
                    port=port,
                    status=response.status,
                ).inc()

                REQUEST_LATENCY.labels(
                    method=request.method, endpoint=request.path, port=port
                ).observe(time.time() - start_time)

                return response
            except Exception:
                # Record error metrics
                HTTP_REQUESTS.labels(
                    method=request.method, endpoint=request.path, port=port, status=500
                ).inc()

                REQUEST_LATENCY.labels(
                    method=request.method, endpoint=request.path, port=port
                ).observe(time.time() - start_time)

                # Re-raise exception
                raise

        return middleware_handler


class PortalServer:
    """Enhanced web portal server for the AI Gateway."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        rate_limiter: RateLimiter | None = None,
    ):
        """Initialize the portal server.

        Args:
            host: Host address to bind to
            port: Port to listen on
            rate_limiter: Optional rate limiter
        """
        self.host = host
        self.port = port
        self.logger = logging.getLogger("portal_server")
        self.rate_limiter = rate_limiter or RateLimiter()
        self.start_time = time.time()

    async def start(self):
        """Start the portal server."""
        app = web.Application(middlewares=[MetricsMiddleware().middleware])

        # API routes
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/status", self._handle_status)
        app.router.add_get("/health", self._handle_health)
        app.router.add_get("/metrics", self._handle_metrics)

        # Configure CORS
        cors = aiohttp_cors.setup(
            app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods=["GET", "POST", "OPTIONS"],
                )
            },
        )

        # Apply CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)

        # Add rate limiting middleware
        @web.middleware
        async def rate_limit_middleware(request, handler):
            if self.rate_limiter.is_rate_limited(
                request.remote or "unknown", request.path
            ):
                return web.json_response(
                    {"status": "error", "message": "Rate limit exceeded"}, status=429
                )
            return await handler(request)

        app.middlewares.append(rate_limit_middleware)

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
            <title>Enhanced AI Gateway Portal</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1, h2 {
                    color: #333;
                }
                .card {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .endpoint {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 3px;
                    font-family: monospace;
                }
                .button {
                    display: inline-block;
                    padding: 8px 16px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-right: 10px;
                }
                .button:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <h1>Enhanced AI Gateway Portal</h1>
            <div class="card">
                <h2>Gateway Status</h2>
                <p>The AI Gateway is running and ready to process requests.</p>
                <p>API endpoint: <span class="endpoint">http://localhost:8081/api</span></p>
                <p>
                    <a href="/status" class="button">View Status</a>
                    <a href="/health" class="button">Health Check</a>
                    <a href="/metrics" class="button">View Metrics</a>
                </p>
            </div>
            
            <div class="card">
                <h2>Available Endpoints</h2>
                <ul>
                    <li><span class="endpoint">http://localhost:8081/api/llm</span> - Language model API</li>
                    <li><span class="endpoint">http://localhost:8081/api/calculator</span> - Calculator tool</li>
                    <li><span class="endpoint">http://localhost:8081/api/weather</span> - Weather tool</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>Documentation</h2>
                <p>For more information on how to use the AI Gateway, check out the documentation.</p>
                <p>Rate limits: LLM API (60 req/min), Calculator (300 req/min), Weather (60 req/min)</p>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    async def _handle_status(self, request):
        """Handle requests to the status page."""
        uptime = int(time.time() - self.start_time)
        port = request.transport.get_extra_info("sockname")[1]

        status = {
            "portal": {
                "status": "running",
                "address": f"http://{self.host}:{port}",
                "uptime_seconds": uptime,
            },
            "gateway": {"status": "running", "address": f"http://{self.host}:8081/api"},
            "environment": {
                "python_version": sys.version,
                "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
            },
        }
        return web.json_response(status)

    async def _handle_health(self, request):
        """Handle health check requests."""
        # Simple health check
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {"portal": "ok", "memory": "ok", "disk": "ok"},
        }

        # Memory check
        try:
            import psutil

            memory = psutil.virtual_memory()
            health_data["checks"]["memory_percent"] = memory.percent
            if memory.percent > 90:
                health_data["checks"]["memory"] = "warning"

            # Disk check
            disk = psutil.disk_usage("/")
            health_data["checks"]["disk_percent"] = disk.percent
            if disk.percent > 90:
                health_data["checks"]["disk"] = "warning"
        except ImportError:
            health_data["checks"]["memory"] = "unknown"
            health_data["checks"]["disk"] = "unknown"

        return web.json_response(health_data)

    async def _handle_metrics(self, request):
        """Handle metrics requests."""
        resp = web.Response(body=generate_latest())
        resp.content_type = "text/plain"
        return resp


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

        # Start gateway
        logger.info(f"Starting AI Gateway on {host}:{port}")
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


async def run_enhanced_portal(
    config_path: str | None = None,
    portal_port: int = 8080,
    api_port: int = 8081,
    debug: bool = False,
) -> None:
    """Run both the enhanced portal and gateway servers.

    Args:
        config_path: Path to configuration file
        portal_port: Port for the portal server
        api_port: Port for the API gateway
        debug: Enable debug mode
    """
    logger.info(
        f"Starting Enhanced Portal on port {portal_port} and API Gateway on port {api_port}"
    )

    # Create rate limiter
    rate_limiter = RateLimiter()

    # Create portal server
    portal = PortalServer(port=portal_port, rate_limiter=rate_limiter)
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
    # Check for environment variables first
    portal_port = int(os.environ.get("PORTAL_PORT", "0")) or 8080
    api_port = int(os.environ.get("API_PORT", "0")) or 8081
    debug_mode = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
    config_path = os.environ.get("CONFIG_PATH")

    # Then check command line arguments (they override env vars)
    parser = argparse.ArgumentParser(
        description="Run Enhanced AI Gateway Portal and API"
    )
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--portal-port",
        type=int,
        default=portal_port,
        help=f"Portal UI port (default: {portal_port})",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=api_port,
        help=f"API Gateway port (default: {api_port})",
    )
    parser.add_argument(
        "--debug", action="store_true", default=debug_mode, help="Enable debug logging"
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            run_enhanced_portal(
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
