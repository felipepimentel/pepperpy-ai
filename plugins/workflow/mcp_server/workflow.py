"""MCP Server Workflow.

This module provides a workflow for running an MCP server.
"""

import asyncio
from typing import Any

from pepperpy.core.logging import get_logger
from pepperpy.core.workflow import WorkflowProvider
from pepperpy.plugin import BasePluginProvider
from pepperpy.plugin.registry import get_plugin


class MCPServerWorkflow(WorkflowProvider, BasePluginProvider):
    """Workflow for running MCP servers."""

    def __init__(self) -> None:
        """Initialize MCP server workflow."""
        super().__init__()
        self.logger = get_logger("workflow.mcp_server")
        self.server = None
        self.llm_provider = None
        self.initialized = False

    async def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the workflow with the given configuration.

        Args:
            config: The configuration to use.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self.initialized:
            return True

        self.logger.info("Initializing MCP server workflow")

        # Server configuration
        host = config.get("host", "0.0.0.0")
        port = config.get("port", 8000)
        provider_type = config.get("provider_type", "http")

        # LLM configuration
        llm_provider_name = config.get("llm_provider", "openai")
        llm_model = config.get("llm_model", "gpt-3.5-turbo")

        try:
            # Get the LLM provider from registry
            llm_config = {"model": llm_model}
            provider_class = get_plugin("llm", llm_provider_name.lower())
            if not provider_class:
                self.logger.error(f"LLM provider not found: {llm_provider_name}")
                return False

            self.llm_provider = provider_class(config=llm_config)

            if not self.llm_provider:
                self.logger.error(f"Failed to create LLM provider: {llm_provider_name}")
                return False

            self.logger.info(
                f"Using LLM provider: {llm_provider_name} with model {llm_model}"
            )

            # Initialize the LLM provider if needed
            if hasattr(self.llm_provider, "initialize"):
                await self.llm_provider.initialize()

            # Create the server provider
            try:
                # Import all at top level to avoid issues
                from pepperpy.mcp.server.providers.http import HTTPServerProvider

                if provider_type == "http":
                    self.server = HTTPServerProvider()
                elif provider_type == "websocket":
                    from pepperpy.mcp.server.providers.websocket import (
                        WebSocketServerProvider,
                    )

                    self.server = WebSocketServerProvider()
                elif provider_type == "grpc":
                    from pepperpy.mcp.server.providers.grpc import GRPCServerProvider

                    self.server = GRPCServerProvider()
                else:
                    self.logger.error(f"Unknown server provider type: {provider_type}")
                    return False
            except ImportError as e:
                self.logger.error(f"Failed to import server provider: {e}")
                return False

            if not self.server:
                self.logger.error(f"Failed to create server provider: {provider_type}")
                return False

            self.logger.info(f"Using MCP server provider: {provider_type}")

            # Configure the server
            server_config = {
                "host": host,
                "port": port,
                "llm_provider": self.llm_provider,
            }

            # Initialize the server with proper error handling
            try:
                # Just assume initialize() method exists and is async
                await self.server.initialize(server_config)
                self.initialized = True
                return True
            except Exception as e:
                self.logger.error(f"Error initializing server: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize MCP server: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources used by the workflow."""
        self.logger.info("Cleaning up MCP server workflow")
        if self.server:
            await self.server.cleanup()
            self.server = None
        if self.llm_provider and hasattr(self.llm_provider, "cleanup"):
            await self.llm_provider.cleanup()
            self.llm_provider = None
        self.initialized = False

    async def execute(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the workflow with the given parameters.

        Args:
            params: Additional parameters for the workflow execution.

        Returns:
            The result of the workflow execution.
        """
        if not self.initialized or not self.server:
            await self.initialize(params or {})
            if not self.initialized or not self.server:
                return {"status": "error", "message": "Server not initialized"}

        self.logger.info("Starting MCP server")

        try:
            # Start the server
            await self.server.start()

            # Create a task to keep the server running
            # This task will run until it's cancelled or the server stops
            server_task = asyncio.create_task(self._server_task())

            return {
                "status": "success",
                "message": "Server started successfully",
                "server_task": server_task,
            }
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return {
                "status": "error",
                "message": f"Failed to start server: {e}",
            }

    async def _server_task(self) -> None:
        """Run the server task.

        This task keeps the server running until it's cancelled.
        """
        if not self.server:
            self.logger.error("Cannot run server task: server is None")
            return

        try:
            # Wait forever (or until cancelled)
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Server task cancelled")
            # Stop the server gracefully
            if self.server:
                await self.server.stop()
        except Exception as e:
            self.logger.error(f"Error in server task: {e}")
            # Stop the server on error
            if self.server:
                await self.server.stop()
