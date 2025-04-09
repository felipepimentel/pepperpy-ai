"""
HTTP client provider for MCP.

This module provides an HTTP client implementation for the MCP protocol.
"""

from pepperpy.mcp.client.providers.http import HTTPClientProvider
from pepperpy.plugin.provider import BasePluginProvider


class HTTPClientAdapter(HTTPClientProvider, BasePluginProvider):
    """HTTP client adapter for MCP."""

    # Use the implementation from the core framework
    pass
