"""
MCP - Model Context Protocol.

This module provides a protocol for model interactions in the PepperPy framework.
"""

from .base import MCPProvider, create_client, create_server
from .protocol import MCPOperationType, MCPRequest, MCPResponse, MCPStatusCode

__all__ = [
    # Base
    "create_client",
    "create_server",
    "MCPProvider",
    # Protocol
    "MCPRequest",
    "MCPResponse",
    "MCPOperationType",
    "MCPStatusCode",
]
