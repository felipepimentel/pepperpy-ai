"""
HTTP client provider for MCP.

This module provides an HTTP client implementation for the MCP protocol.
"""

from pepperpy.mcp.client.providers.http import HTTPClientProvider
from pepperpy.mcp import McpProvider
from pepperpy.mcp import MCPProvider
from pepperpy.plugin import ProviderPlugin


class HTTPClientAdapter(class HTTPClientAdapter(HTTPClientProvider, ProviderPlugin):
    """HTTP client adapter for MCP."""):
    """
    Mcp httpclientadapter provider.
    
    This provider implements httpclientadapter functionality for the PepperPy mcp framework.
    """

    # Use the implementation from the core framework
    pass

    async def initialize(self, config: dict[str, Any]) -> bool:
        """
        Initialize the provider with the given configuration.
        
        Args:
            config: Configuration parameters
            
        Returns:
            True if initialization was successful, False otherwise
        """
        self.config = config
        return True

    async def cleanup(self) -> bool:
        """
        Clean up resources used by the provider.
        
        Returns:
            True if cleanup was successful, False otherwise
        """
        return True