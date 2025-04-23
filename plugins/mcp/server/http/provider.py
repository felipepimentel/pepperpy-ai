"""
HTTP server provider for MCP.

This module provides an HTTP server implementation for the MCP protocol.
"""

from pepperpy.mcp.server.providers.http import HTTPServerProvider
from pepperpy.mcp import McpProvider
from pepperpy.mcp import MCPProvider
from pepperpy.plugin import ProviderPlugin


class HTTPServerAdapter(class HTTPServerAdapter(HTTPServerProvider, ProviderPlugin):
    """HTTP server adapter for MCP."""):
    """
    Mcp httpserveradapter provider.
    
    This provider implements httpserveradapter functionality for the PepperPy mcp framework.
    """

    # Use the implementation from the core framework
    pass
