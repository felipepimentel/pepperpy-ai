"""
HTTP server provider for MCP.

This module provides an HTTP server implementation for the MCP protocol.
"""

from pepperpy.mcp.server.providers.http import HTTPServerProvider
from pepperpy.plugin.provider import BasePluginProvider


class HTTPServerAdapter(HTTPServerProvider, BasePluginProvider):
    """HTTP server adapter for MCP."""

    # Use the implementation from the core framework
    pass
