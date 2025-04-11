#!/usr/bin/env python3
"""
Test script for running the AI Gateway.

This script demonstrates how to run an AI Gateway with basic authentication
and routing capabilities, supporting multiple AI providers.
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

# Import our new adapter
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


# Simple mock LLM provider for testing
class MockLLMProvider:
    """Mock LLM provider for testing the AI Gateway."""

    def __init__(self, **kwargs):
        """Initialize the mock provider."""
        self.config = kwargs
        self.initialized = False
        self.logger = logging.getLogger("mock_llm")
        self.model_name = self.config.get("model", "gpt-3.5-turbo")

    async def initialize(self):
        """Initialize the provider."""
        self.initialized = True
        self.logger.info(f"Mock LLM Provider initialized with model: {self.model_name}")

    async def cleanup(self):
        """Clean up resources."""
        self.initialized = False
        self.logger.info("Mock LLM Provider cleaned up")

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

            # Generate a mock response based on the input
            return {
                "status": "success",
                "outputs": {
                    "content": f"Mock response from {self.model_name}: I received your message: '{latest_message}'"
                },
                "model": self.model_name,
            }
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}


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
    logger = logging.getLogger("ai_gateway_test")

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
            logger.info("Loading MCP server provider...")
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

                # Register tool handlers
                try:
                    # Register calculate handler
                    async def calculate_handler(request):
                        try:
                            expression = request.inputs.get("expression", "")
                            result = eval(
                                expression
                            )  # In production, use a safer method
                            return {"result": str(result)}
                        except Exception as e:
                            return {"error": str(e)}

                    # Register weather handler
                    async def weather_handler(request):
                        try:
                            location = request.inputs.get("location", "")
                            # Mock weather data
                            return {
                                "weather": {
                                    "location": location,
                                    "temperature": 22,
                                    "condition": "partly cloudy",
                                }
                            }
                        except Exception as e:
                            return {"error": str(e)}

                    # Register translate handler
                    async def translate_handler(request):
                        try:
                            text = request.inputs.get("text", "")
                            target_language = request.inputs.get(
                                "target_language", "es"
                            )
                            # Mock translation
                            return {"translated_text": f"[{target_language}] {text}"}
                        except Exception as e:
                            return {"error": str(e)}

                    # Register handlers with server
                    await mcp_server.register_handler(
                        "calculate", calculate_handler, is_stream=False
                    )
                    await mcp_server.register_handler(
                        "get_weather", weather_handler, is_stream=False
                    )
                    await mcp_server.register_handler(
                        "translate", translate_handler, is_stream=False
                    )
                    logger.info("Registered tool handlers with MCP server")
                except Exception as e:
                    logger.error(f"Failed to register tool handlers: {e}")

                # Create and initialize the adapter
                mcp_adapter = MCPServerAdapter(mcp_server)
                await mcp_adapter.initialize()

                # Register the MCP server with the router
                await routing_provider.register_backend("llm", mcp_adapter)
                llm_providers.append(mcp_adapter)
                logger.info("Registered MCP server provider")

        except Exception as e:
                logger.error(f"Failed to initialize MCP server: {e}")
                import traceback

                logger.error(traceback.format_exc())

                # Fall back to mock provider
                logger.info("Falling back to mock provider...")
                use_mcp = False

        if not use_mcp:
            # Create mock LLM provider
            logger.info("Creating mock LLM provider...")
            llm_provider = MockLLMProvider(model="gpt-3.5-turbo")
            await llm_provider.initialize()

            # Register the LLM provider with the router
            await routing_provider.register_backend("llm", llm_provider)
            llm_providers.append(llm_provider)
            logger.info("Registered mock LLM provider")

            # Create a second model
            logger.info("Creating another mock LLM provider...")
            llm_provider2 = MockLLMProvider(model="gpt-4")
            await llm_provider2.initialize()

            # Register the second LLM provider with the router
            await routing_provider.register_backend("gpt4", llm_provider2)
            llm_providers.append(llm_provider2)
            logger.info("Registered second mock LLM provider")

        # Start the gateway
        logger.info("Starting the gateway server...")
        await routing_provider.configure(host, port)
        await routing_provider.start()

        # Keep the server running until interrupted
        logger.info(f"AI Gateway is running at http://{host}:{port}")
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

            # Clean up all providers
            for provider in llm_providers:
                await provider.cleanup()

            logger.info("Gateway stopped")

    except Exception as e:
        logger.error(f"Error running AI Gateway: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return


def main() -> int:
    """Command-line entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run an AI Gateway test server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to listen on (default: 8080)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--use-mcp", action="store_true", help="Use MCP server instead of mock"
    )
    parser.add_argument(
        "--test", action="store_true", help="Run a test request after startup"
    )

    args = parser.parse_args()

    try:
        if args.test:
            asyncio.run(test_gateway(args.host, args.port, args.debug, args.use_mcp))
            return 0
        else:
            asyncio.run(run_gateway(args.host, args.port, args.debug, args.use_mcp))
        return 0
    except KeyboardInterrupt:
        print("Gateway stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


async def test_gateway(
    host: str, port: int, debug: bool = False, use_mcp: bool = False
) -> None:
    """Run the gateway with a test request.

    Args:
        host: Host address
        port: Port number
        debug: Enable debug mode
        use_mcp: Use MCP server
    """
    # Start the gateway in background
    gateway_task = asyncio.create_task(run_gateway(host, port, debug, use_mcp))

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

    # Cancel the gateway task after test
    gateway_task.cancel()
    try:
        await gateway_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    sys.exit(main())
