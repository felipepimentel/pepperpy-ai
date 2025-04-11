#!/usr/bin/env python3
"""
Simple test of running a server on multiple ports.
"""

import asyncio
import logging

from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("multi_port_test")


async def handle_status(request):
    """Handle status requests."""
    port = request.transport.get_extra_info("sockname")[1]
    return web.json_response({"status": "running", "port": port})


async def handle_root(request):
    """Handle root requests."""
    port = request.transport.get_extra_info("sockname")[1]
    return web.Response(
        text=f"<html><body><h1>Server running on port {port}</h1></body></html>",
        content_type="text/html",
    )


async def run_server_on_port(port):
    """Run a server on the specified port."""
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/status", handle_status)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Server started on port {port}")

    # Return the runner so we can close it later
    return runner


async def main():
    """Run servers on multiple ports."""
    ports = [8090, 8091]
    logger.info(f"Starting servers on ports: {ports}")

    # Start servers on each port
    runners = []
    for port in ports:
        runner = await run_server_on_port(port)
        runners.append(runner)

    # Keep the servers running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Clean up
        for runner in runners:
            await runner.cleanup()
        logger.info("Servers stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servers stopped by user")
