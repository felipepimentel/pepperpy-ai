#!/usr/bin/env python3
"""
Unified script to run both the MCP server and the AI Gateway.

This simplifies the setup by running both components in one process.
"""

import argparse
import asyncio
import json
import logging
import os
import sys

# Add the project root to sys.path if needed
if os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "..")):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import required components
import importlib.util


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


async def run_unified_gateway(host: str, port: int, debug: bool = False) -> None:
    """Run both the MCP server and AI Gateway in a unified process.

    Args:
        host: The host to bind to
        port: The port to listen on
        debug: Whether to enable debug logging
    """
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logging(level=log_level)
    logger = logging.getLogger("unified_gateway")

    logger.info(f"Starting Unified Gateway on {host}:{port}")

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

        # Create and register a mock LLM provider
        logger.info("Creating LLM provider...")

        # Simple mock LLM provider for testing
        class SimpleLLMProvider:
            """Simple LLM provider for the unified gateway."""

            def __init__(self, **kwargs):
                """Initialize the provider."""
                self.model = kwargs.get("model", "gpt-3.5-turbo")
                self.initialized = False
                self.logger = logging.getLogger("simple_llm")

            async def initialize(self):
                """Initialize the provider."""
                self.initialized = True
                self.logger.info(
                    f"Simple LLM Provider initialized with model: {self.model}"
                )

            async def cleanup(self):
                """Clean up resources."""
                self.initialized = False
                self.logger.info("Simple LLM Provider cleaned up")

            async def execute(self, data):
                """Execute a request.

                Args:
                    data: Request data

                Returns:
                    Response data
                """
                if not self.initialized:
                    return {"status": "error", "message": "Provider not initialized"}

                try:
                    # Log request
                    self.logger.info(f"Received request: {data}")

                    # Extract data from the request
                    operation = data.get("operation", "chat")
                    messages = data.get("messages", [])

                    if operation != "chat":
                        return {
                            "status": "error",
                            "message": f"Unsupported operation: {operation}",
                        }

                    if not messages:
                        return {"status": "error", "message": "No messages provided"}

                    # Get the latest user message
                    latest_message = None
                    for msg in reversed(messages):
                        if msg.get("role") == "user":
                            latest_message = msg.get("content", "")
                            break

                    if not latest_message:
                        return {"status": "error", "message": "No user message found"}

                    # Generate a simple response based on the input
                    response = f"This is a response to: '{latest_message}' from model {self.model}"

                    return {
                        "status": "success",
                        "outputs": {"content": response},
                        "model": self.model,
                    }
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    import traceback

                    self.logger.error(traceback.format_exc())
                    return {"status": "error", "message": str(e)}

        # Create the provider instances
        llm_provider = SimpleLLMProvider(model="gpt-3.5-turbo")
        await llm_provider.initialize()

        llm_provider2 = SimpleLLMProvider(model="gpt-4")
        await llm_provider2.initialize()

        # Register the providers with the routing provider
        await routing_provider.register_backend("llm", llm_provider)
        logger.info("Registered llm provider")

        await routing_provider.register_backend("gpt4", llm_provider2)
        logger.info("Registered gpt4 provider")

        # Register a custom tool handler
        logger.info("Registering calculate tool...")

        class CalculateTool:
            """Calculator tool provider."""

            def __init__(self):
                """Initialize the tool."""
                self.initialized = False
                self.logger = logging.getLogger("calculator_tool")

            async def initialize(self):
                """Initialize the tool."""
                self.initialized = True
                self.logger.info("Calculator tool initialized")

            async def cleanup(self):
                """Clean up resources."""
                self.initialized = False
                self.logger.info("Calculator tool cleaned up")

            async def execute(self, data):
                """Execute a calculation.

                Args:
                    data: Request data with expression

                Returns:
                    Calculation result
                """
                try:
                    # Log request
                    self.logger.info(f"Received calculation request: {data}")

                    # Extract the expression
                    expression = data.get("expression", "")

                    if not expression:
                        return {"status": "error", "message": "No expression provided"}

                    # Calculate the result (in production, use a safer method)
                    result = eval(expression)

                    return {"status": "success", "outputs": {"result": str(result)}}
                except Exception as e:
                    self.logger.error(f"Error calculating: {e}")
                    return {"status": "error", "message": str(e)}

        # Create and register the calculator tool
        calculator = CalculateTool()
        await calculator.initialize()
        await routing_provider.register_backend("calculator", calculator)
        logger.info("Registered calculator tool")

        # Start the gateway
        logger.info("Starting the gateway server...")
        await routing_provider.configure(host, port)
        await routing_provider.start()

        # Keep the server running until interrupted
        logger.info(f"Unified Gateway is running at http://{host}:{port}")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Gateway shutting down...")
        finally:
            # Clean up resources
            logger.info("Stopping the gateway...")
            await routing_provider.stop()
            await routing_provider.cleanup()
            await auth_provider.cleanup()
            await llm_provider.cleanup()
            await llm_provider2.cleanup()
            await calculator.cleanup()
            logger.info("Gateway stopped")

    except Exception as e:
        logger.error(f"Error running Unified Gateway: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return


def main() -> int:
    """Command-line entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run a Unified Gateway server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8081, help="Port to listen on (default: 8081)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--test", action="store_true", help="Run a test request after startup"
    )

    args = parser.parse_args()

    try:
        if args.test:
            asyncio.run(test_gateway(args.host, args.port, args.debug))
            return 0
        else:
            asyncio.run(run_unified_gateway(args.host, args.port, args.debug))
            return 0
    except KeyboardInterrupt:
        print("Gateway stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


async def test_gateway(host: str, port: int, debug: bool = False) -> None:
    """Run the gateway with a test request.

    Args:
        host: Host address
        port: Port number
        debug: Enable debug mode
    """
    # Start the gateway in background
    gateway_task = asyncio.create_task(run_unified_gateway(host, port, debug))

    # Wait for server to start
    await asyncio.sleep(2)

    # Create a test client
    import aiohttp

    async with aiohttp.ClientSession() as session:
        # Send a test request
        headers = {"X-API-Key": "test-key-1"}
        url = f"http://{host}:{port}/api/llm"
        data = {
            "operation": "chat",
            "messages": [{"role": "user", "content": "Hello, AI Gateway!"}],
        }

        print(f"\n\nSending test request to {url}...")
        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Response status: {response.status}")
                result = await response.json()
                print(f"Response data: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Error during test: {e}")

        # Test calculator tool
        url = f"http://{host}:{port}/api/calculator"
        data = {"expression": "2 + 2 * 10"}

        print(f"\n\nSending calculator request to {url}...")
        try:
            async with session.post(url, json=data, headers=headers) as response:
                print(f"Response status: {response.status}")
                result = await response.json()
                print(f"Response data: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Error during test: {e}")

    # Cancel the gateway task after test
    gateway_task.cancel()
    try:
        await gateway_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    sys.exit(main())
