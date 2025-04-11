#!/usr/bin/env python3
"""
Multi-port AI Gateway server.

This script allows running the AI Gateway on multiple ports simultaneously.
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


async def run_gateway_on_port(
    config_path: str | None = None,
    host: str = "0.0.0.0",
    port: int = 8080,
    debug: bool = False,
) -> None:
    """Run an AI Gateway on a specific port.

    Args:
        config_path: Path to configuration file
        host: Host address to bind to
        port: Port to listen on
        debug: Enable debug mode
    """
    logger = logging.getLogger(f"gateway_port_{port}")

    try:
        # Load configuration
        config = load_config(config_path)

        # Setup logging
        if debug:
            config.setdefault("logging", {})["level"] = "debug"
        setup_logging(config)

        # Create gateway
        logger.info(f"Creating AI Gateway for port {port}")

        # Create auth provider
        auth_config = config.get("auth", {})
        auth_provider = await create_auth_provider(
            auth_config.get("provider", "basic"), **auth_config
        )
        await auth_provider.initialize()

        # Create routing provider with specific port
        routing_config = config.get("routing", {}).copy()
        routing_config["host"] = host
        routing_config["port"] = port

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
        logger.info(f"Gateway on port {port} shutting down...")
        await gateway.stop()
        await routing_provider.cleanup()
        await auth_provider.cleanup()
    except Exception as e:
        logger.error(f"Error running gateway on port {port}: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def run_multi_port_gateway(
    config_path: str | None = None, ports: list[int] | None = None, debug: bool = False
) -> None:
    """Run the AI Gateway on multiple ports simultaneously.

    Args:
        config_path: Path to configuration file
        ports: List of ports to listen on
        debug: Enable debug mode
    """
    logger = logging.getLogger("multi_port_gateway")

    if ports is None:
        ports = [8080]

    logger.info(f"Starting AI Gateway on ports: {', '.join(map(str, ports))}")

    # Create tasks for each port
    tasks = []
    for port in ports:
        task = asyncio.create_task(
            run_gateway_on_port(config_path, "0.0.0.0", port, debug)
        )
        tasks.append(task)

    try:
        # Wait for all tasks to complete (they won't without cancellation)
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down all gateways...")
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        # Wait for all tasks to be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All gateways stopped")


def main() -> int:
    """Command-line entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run AI Gateway on multiple ports")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--ports",
        nargs="+",
        type=int,
        default=[8080, 8081],
        help="Ports to listen on (default: 8080 8081)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    try:
        asyncio.run(run_multi_port_gateway(args.config, args.ports, args.debug))
        return 0
    except KeyboardInterrupt:
        print("Gateway stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
