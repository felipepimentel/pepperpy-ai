"""
HTTP client provider for MCP.

This module provides an HTTP client implementation for the MCP protocol.
"""

from typing import Any, Dict, Optional

from mcp import ClientSession, SSEServer, types
from pepperpy.plugin import ProviderPlugin


class HTTPClientAdapter(ProviderPlugin):
    """HTTP client adapter for MCP."""

    def __init__(self, **config: Any) -> None:
        """Initialize the client adapter.
        
        Args:
            **config: Configuration options for the client
        """
        super().__init__(**config)
        self.server_url = config.get("server_url", "http://localhost:8000")
        self.session: Optional[ClientSession] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the MCP client."""
        if self._initialized:
            return
        
        # Create MCP client session using the official library
        server = SSEServer(self.server_url)
        self.session = ClientSession(server)
        
        # Initialize the connection
        await self.session.initialize()
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self._initialized = False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            arguments: The arguments to pass to the tool
            
        Returns:
            The result of the tool call
            
        Raises:
            RuntimeError: If the client is not initialized or the tool call fails
        """
        if not self._initialized or not self.session:
            raise RuntimeError("Client not initialized")
        
        # Call the tool using the official MCP library
        result = await self.session.call_tool(tool_name, arguments)
        return result
    
    async def read_resource(self, resource_path: str) -> tuple[bytes, str]:
        """Read a resource from the MCP server.
        
        Args:
            resource_path: The path of the resource to read
            
        Returns:
            A tuple of (content, mime_type)
            
        Raises:
            RuntimeError: If the client is not initialized or the resource read fails
        """
        if not self._initialized or not self.session:
            raise RuntimeError("Client not initialized")
        
        # Read the resource using the official MCP library
        content, mime_type = await self.session.read_resource(resource_path)
        return content, mime_type