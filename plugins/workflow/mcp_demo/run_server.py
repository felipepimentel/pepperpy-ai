#!/usr/bin/env python3
"""MCP Server Runner.

Standalone script to run just the MCP server component for testing purposes.
"""

import argparse
import asyncio
import importlib
import os
import signal
import sys

from pepperpy.core.logging import get_logger
from pepperpy.mcp.protocol import MCPRequest, MCPResponse, MCPStatusCode
from pepperpy.mcp.server.providers.http import HTTPServerProvider

logger = get_logger("mcp.server.runner")

# Make sure the workflow module can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


class MCPServerRunner:
    """Simple runner for MCP server with demo tools."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        api_key: str | None = None,
    ) -> None:
        """Initialize the MCP server runner.

        Args:
            host: Server host
            port: Server port
            llm_provider: LLM provider type
            llm_model: LLM model ID
            api_key: API key for LLM provider
        """
        self.host = host
        self.port = port
        self.llm_provider_type = llm_provider
        self.llm_model = llm_model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

        self.server: HTTPServerProvider | None = None
        self.llm_provider = None
        self.initialized = False
        self.running = False
        self.shutdown_requested = False

        # Import the workflow module dynamically
        self.workflow_module = importlib.import_module("workflow")

    async def initialize(self) -> None:
        """Initialize server and resources."""
        if self.initialized:
            return

        # Initialize server
        self.server = HTTPServerProvider(host=self.host, port=self.port)
        await self.server.initialize()

        # Initialize LLM provider using the class from the dynamically imported module
        self.llm_provider = self.workflow_module.SimpleLLMAdapter(
            provider_type=self.llm_provider_type,
            model=self.llm_model,
            api_key=self.api_key,
        )
        await self.llm_provider.initialize()

        # Register tools with the server
        await self._register_tools()

        self.initialized = True
        logger.info(f"MCP server initialized at {self.host}:{self.port}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        if self.server and hasattr(self.server, "running") and self.server.running:
            logger.info("Stopping server...")
            await self.server.stop()

        if self.server:
            await self.server.cleanup()
            self.server = None

        if self.llm_provider:
            await self.llm_provider.cleanup()
            self.llm_provider = None

        self.initialized = False
        self.running = False
        logger.info("MCP server cleaned up")

    async def _register_tools(self) -> None:
        """Register tools with the server."""
        if not self.server:
            return

        # Register the LLM provider for chat
        await self.server.register_model(
            model_id=self.llm_model, model=self.llm_provider
        )

        # Register custom tool handlers
        await self.server.register_handler(
            "calculate", self._tool_calculate, is_stream=False
        )
        await self.server.register_handler(
            "get_weather", self._tool_weather, is_stream=False
        )
        await self.server.register_handler(
            "translate", self._tool_translate, is_stream=False
        )

        logger.info("Registered all tools with the server")

    async def _tool_calculate(self, request: MCPRequest) -> MCPResponse:
        """Handle calculate tool requests."""
        try:
            messages = request.inputs.get("messages", [])
            if not messages:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="No messages provided",
                )

            content = messages[-1].get("content", "")
            if not content.startswith("calculate:"):
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid calculate request format",
                )

            expression = content.replace("calculate:", "").strip()
            result = eval(expression)  # In production, use a safer evaluation method

            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"result": str(result)},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def _tool_weather(self, request: MCPRequest) -> MCPResponse:
        """Handle weather tool requests."""
        try:
            messages = request.inputs.get("messages", [])
            if not messages:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="No messages provided",
                )

            content = messages[-1].get("content", "")
            if not content.startswith("get_weather:"):
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid weather request format",
                )

            location = content.replace("get_weather:", "").strip()
            # Mock weather data - replace with actual API call
            weather = {"location": location, "temperature": 20, "condition": "sunny"}

            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"weather": weather},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def _tool_translate(self, request: MCPRequest) -> MCPResponse:
        """Handle translate tool requests."""
        try:
            messages = request.inputs.get("messages", [])
            if not messages:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="No messages provided",
                )

            content = messages[-1].get("content", "")
            if not content.startswith("translate:"):
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid translate request format",
                )

            # Parse "translate: text to target_lang"
            parts = content.replace("translate:", "").strip().split(" to ")
            if len(parts) != 2:
                return MCPResponse(
                    request_id=request.request_id,
                    model_id=request.model_id,
                    status=MCPStatusCode.ERROR,
                    error="Invalid translate format. Use: translate: text to target_lang",
                )

            text, target_lang = parts
            # Mock translation - replace with actual API call
            translated_text = f"[{target_lang}] {text}"

            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.SUCCESS,
                outputs={"translated_text": translated_text},
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                model_id=request.model_id,
                status=MCPStatusCode.ERROR,
                error=str(e),
            )

    async def run(self) -> None:
        """Run the server until interrupted."""
        if not self.initialized:
            await self.initialize()

        if self.running:
            logger.warning("Server is already running")
            return

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        try:
            if not self.server:
                logger.error("Server not initialized properly")
                return

            logger.info(f"Starting MCP server on {self.host}:{self.port}...")
            await self.server.start()
            self.running = True

            logger.info("MCP server is running. Press Ctrl+C to stop.")

            # Keep running until shutdown is requested
            while not self.shutdown_requested:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error running server: {e}")
        finally:
            if self.running:
                await self.cleanup()

    async def shutdown(self) -> None:
        """Request server shutdown."""
        if not self.shutdown_requested:
            logger.info("Shutdown requested, stopping server...")
            self.shutdown_requested = True


async def main() -> int:
    """Run the MCP server.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(description="MCP Server Runner")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--llm-provider", default="openai", help="LLM provider (default: openai)"
    )
    parser.add_argument(
        "--llm-model",
        default="gpt-3.5-turbo",
        help="LLM model (default: gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--api-key",
        help="API key for LLM provider (defaults to OPENAI_API_KEY env variable)",
    )

    args = parser.parse_args()

    try:
        server_runner = MCPServerRunner(
            host=args.host,
            port=args.port,
            llm_provider=args.llm_provider,
            llm_model=args.llm_model,
            api_key=args.api_key,
        )
        await server_runner.run()
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
