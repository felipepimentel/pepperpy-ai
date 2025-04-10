"""MCP Server Adapter for AI Gateway.

This adapter makes the MCP server compatible with the AI Gateway routing provider.
"""

import logging
from typing import Any

from pepperpy.mcp.protocol import (
    MCPOperationType,
    MCPRequest,
    MCPResponse,
    MCPStatusCode,
)

logger = logging.getLogger(__name__)


class MCPServerAdapter:
    """Adapter for MCP Server to work with the AI Gateway routing provider.

    The routing provider expects an 'execute' method, but the MCPServerRunner
    doesn't provide one. This adapter translates between the interfaces.
    """

    def __init__(self, mcp_server: Any) -> None:
        """Initialize the adapter.

        Args:
            mcp_server: The MCP server instance
        """
        self.server = mcp_server
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """Initialize the adapter."""
        if self.initialized:
            return

        # If the server isn't initialized, initialize it
        if not getattr(self.server, "initialized", True):
            await self.server.initialize()

        self.initialized = True
        self.logger.info("MCP Server Adapter initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if not self.initialized:
            return

        # Only clean up the server if we initialized it
        if hasattr(self.server, "cleanup"):
            await self.server.cleanup()

        self.initialized = False
        self.logger.info("MCP Server Adapter cleaned up")

    async def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        """Execute a request through the MCP server.

        Args:
            data: The request data containing operation and parameters

        Returns:
            The response data
        """
        try:
            operation = data.get("operation")
            if not operation:
                return {"status": "error", "message": "No operation specified"}

            # Handle chat operation
            if operation == "chat":
                return await self._handle_chat(data)

            # Handle tool operations
            elif operation in ["calculate", "get_weather", "translate"]:
                return await self._handle_tool(operation, data)

            # Unknown operation
            else:
                return {"status": "error", "message": f"Unknown operation: {operation}"}

        except Exception as e:
            self.logger.error(f"Error executing request: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}

    async def _handle_chat(self, data: dict[str, Any]) -> dict[str, Any]:
        """Handle a chat request.

        Args:
            data: The chat request data

        Returns:
            The chat response
        """
        messages = data.get("messages", [])
        model = data.get("model", "gpt-3.5-turbo")

        if not messages:
            return {"status": "error", "message": "No messages provided"}

        # Create an MCP request
        request = MCPRequest(
            request_id="chat-" + str(hash(str(messages))),
            model_id=model,
            operation=MCPOperationType.CHAT,
            inputs={"messages": messages},
        )

        # Process the request through the MCP server
        if hasattr(self.server, "process_request"):
            response = await self.server.process_request(request)
        else:
            # Fallback for different server interface
            response = await self.server.handle_request(request)

        # Transform the response to the expected format
        if isinstance(response, MCPResponse):
            if response.status == MCPStatusCode.SUCCESS:
                return {
                    "status": "success",
                    "outputs": {
                        "content": response.outputs.get("content", ""),
                        "messages": response.outputs.get("messages", []),
                    },
                    "model": model,
                }
            else:
                return {"status": "error", "message": response.error or "Unknown error"}
        else:
            # Handle dictionary response format
            return {
                "status": "success" if response.get("status") == "success" else "error",
                "outputs": response.get("outputs", {}),
                "message": response.get("error", ""),
            }

    async def _handle_tool(
        self, operation: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle a tool request.

        Args:
            operation: The tool operation name
            data: The tool request data

        Returns:
            The tool response
        """
        # Extract parameters based on the operation
        inputs = {}
        if operation == "calculate":
            inputs["expression"] = data.get("expression", "")
        elif operation == "get_weather":
            inputs["location"] = data.get("location", "")
        elif operation == "translate":
            inputs["text"] = data.get("text", "")
            inputs["target_language"] = data.get("target_language", "")

        # Create an MCP request - use string for operation since it's not a standard MCPOperationType
        request = MCPRequest(
            request_id=f"{operation}-{hash(str(inputs))}",
            model_id="default",
            operation=MCPOperationType.COMPLETION,  # Use COMPLETION as fallback for custom operations
            inputs=inputs,
            parameters={"tool_name": operation},  # Add tool name as parameter
        )

        # Process the request through the MCP server
        if hasattr(self.server, "process_request"):
            response = await self.server.process_request(request)
        else:
            # Fallback for different server interface
            response = await self.server.handle_request(request)

        # Transform the response to the expected format
        if isinstance(response, MCPResponse):
            if response.status == MCPStatusCode.SUCCESS:
                return {"status": "success", "outputs": response.outputs}
            else:
                return {"status": "error", "message": response.error or "Unknown error"}
        else:
            # Handle dictionary response format
            return {
                "status": "success" if response.get("status") == "success" else "error",
                "outputs": response.get("outputs", {}),
                "message": response.get("error", ""),
            }
