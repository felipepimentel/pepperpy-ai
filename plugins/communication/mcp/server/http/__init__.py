"""
HTTP server implementation for MCP.

This module provides an HTTP server implementation using the official MCP library.
"""

__version__ = "0.1.0"

from .provider import HTTPServerAdapter

__all__ = ["HTTPServerAdapter"]
