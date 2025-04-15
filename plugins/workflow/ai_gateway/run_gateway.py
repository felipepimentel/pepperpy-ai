#!/usr/bin/env python3
"""
Script for running the AI Gateway.

This script demonstrates how to run an AI Gateway with authentication
and routing capabilities, supporting multiple AI providers.
"""

import argparse
import asyncio
import logging
import os
import sys

# Add the project root to sys.path if needed
if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "..")):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import required components
import importlib.util

# Import our adapter
from plugins.workflow.ai_gateway.mcp_adapter import MCPServerAdapter


# Configure logging
def setup_logging(level=logging.INFO):
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# Helper function to load plugin providers
async def load_plugin_provider(plugin_type, provider_name, **config):
    """Load a plugin provider by type and name."""
    module_path = f"plugins.{plugin_type}.{provider_name}.provider"
    try:
        module = importlib.import_module(module_path)

        # Try to find the provider class
        for attr_name in dir(module):
            if attr_name.endswith("Provider") and not attr_name.startswith("_"):
                provider_class = getattr(module, attr_name)
                return provider_class(**config)

        raise ValueError(f"Could not find provider class in {module_path}")
    except ImportError as e:
        raise ImportError(
            f"Could not load plugin provider {plugin_type}/{provider_name}: {e}"
        )


async def run_gateway(
    host: str, port: int, debug: bool = False, use_mcp: bool = False
) -> None:
    """Run the AI Gateway with minimal components.

    Args:
        host: The host to bind to
        port: The port to listen on
        debug: Whether to enable debug logging
        use_mcp: Whether to use the MCP server
    """
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(level=log_level)
    logger = logging.getLogger("ai_gateway")

    logger.info(f"Starting AI Gateway on {host}:{port}")

    try:
        # Load the auth provider
        logger.info("Loading authentication provider...")
        auth_provider = await load_plugin_provider(
            "auth",
            "basic",
            api_keys={
                "test-key-1": "user1",
                "test-key-2": "user2",
            },
        )
        await auth_provider.initialize()

        # Load the routing provider
        logger.info("Loading routing provider...")
        routing_provider = await load_plugin_provider(
            "routing", "basic", host=host, port=port, log_requests=True
        )
        await routing_provider.initialize()

        # Connect the auth provider to the routing provider
        await routing_provider.set_auth_provider(auth_provider)

        # Register backend providers
        llm_providers = []

        if use_mcp:
            # Use MCP server with adapter
            logger.info("Using MCP server as provider...")
            try:
                from pepperpy.mcp.server.providers.http import HTTPServerProvider

                # Create and initialize the MCP server
                mcp_server = HTTPServerProvider(host="0.0.0.0", port=8000)
                await mcp_server.initialize()

                # Register OpenAI model with the server
                try:
                    logger.info("Registering OpenAI model with MCP server...")
                    from pepperpy.mcp.llm.providers.openai import OpenAIProvider

                    openai_provider = OpenAIProvider(
                        api_key=os.environ.get("OPENAI_API_KEY", ""),
                        model="gpt-3.5-turbo",
                    )
                    await openai_provider.initialize()

                    # Register the model with the MCP server
                    await mcp_server.register_model("gpt-3.5-turbo", openai_provider)
                    logger.info("Successfully registered OpenAI model with MCP server")
                except Exception as e:
                    logger.error(f"Failed to register OpenAI model: {e}")
                    return

                # Create MCP adapter
                mcp_adapter = MCPServerAdapter(mcp_server=mcp_server)
                await mcp_adapter.initialize()

                # Register the adapter with the routing provider
                await routing_provider.register_provider(mcp_adapter, "mcp")
                logger.info("Registered MCP adapter with the routing provider")
            except Exception as e:
                logger.error(f"Failed to initialize MCP server: {e}")
                return
        else:
            logger.error("MCP server usage is required. Use --use-mcp flag.")
            return

        # Start the gateway
        try:
            # Keep the server running
            logger.info("AI Gateway is running. Press Ctrl+C to exit.")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt. Shutting down...")
        finally:
            # Clean up resources
            logger.info("Cleaning up resources...")
            for provider in llm_providers:
                await provider.cleanup()

            await auth_provider.cleanup()
            await routing_provider.cleanup()
    except Exception as e:
        logger.error(f"Error initializing AI Gateway: {e}")
        import traceback

        logger.error(traceback.format_exc())


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run AI Gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--use-mcp", action="store_true", help="Use MCP server")

    args = parser.parse_args()
    await run_gateway(
        host=args.host, port=args.port, debug=args.debug, use_mcp=args.use_mcp
    )


if __name__ == "__main__":
    asyncio.run(main())
