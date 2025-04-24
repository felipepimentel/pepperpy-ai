"""
HTTP server provider for MCP.

This module provides an HTTP server implementation for the MCP protocol.
"""

from typing import Any

from mcp.server.fastmcp import FastMCP
from pepperpy.plugin import ProviderPlugin


class HTTPServerAdapter(ProviderPlugin):
    """HTTP server adapter for MCP."""

    def __init__(self, **config: Any) -> None:
        """Initialize the server adapter.
        
        Args:
            **config: Configuration options for the server
        """
        super().__init__(**config)
        self.server_name = config.get("server_name", "PepperPy MCP Server")
        self.mcp_server = FastMCP(self.server_name)
        self.port = int(config.get("port", 8000))
        self.host = config.get("host", "127.0.0.1")
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the MCP server."""
        if self._initialized:
            return
        
        # Set up server configuration from config
        # This will be expanded based on the actual needs
        
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self._initialized = False
    
    def run(self) -> None:
        """Run the MCP server.
        
        This method starts the server and blocks until it is stopped.
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized")
        
        # Start the server using the official MCP library
        self.mcp_server.run(host=self.host, port=self.port)
