"""
Base MCP interfaces and factories.

This module defines the core interfaces and factory functions for MCP.
"""

from abc import abstractmethod
from typing import Any, AsyncGenerator, Protocol, TypeVar

from pepperpy.core.logging import get_logger
from pepperpy.plugin.base import PepperpyPlugin
from .protocol import MCPRequest, MCPResponse

logger = get_logger(__name__)
T = TypeVar('T')

class MCPProvider(PepperpyPlugin, Protocol):
    """Base protocol for MCP providers."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        ...
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources."""
        ...

# Factory functions to create clients and servers
async def create_client(provider_type: str = "default", **config) -> Any:
    """Create an MCP client.
    
    Args:
        provider_type: Type of client provider to create
        **config: Provider configuration
        
    Returns:
        An initialized MCP client provider
        
    Raises:
        ValueError: If the provider type is unknown
    """
    from .client.base import MCPClientProvider
    
    logger.info(f"Creating MCP client provider: {provider_type}")
    
    if provider_type == "websocket":
        from .client.providers.websocket import WebSocketClientProvider
        provider = WebSocketClientProvider(**config)
    elif provider_type == "grpc":
        from .client.providers.grpc import GRPCClientProvider
        provider = GRPCClientProvider(**config)
    elif provider_type == "default" or provider_type == "http":
        from .client.providers.http import HTTPClientProvider
        provider = HTTPClientProvider(**config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    await provider.initialize()
    return provider

async def create_server(provider_type: str = "default", **config) -> Any:
    """Create an MCP server.
    
    Args:
        provider_type: Type of server provider to create
        **config: Provider configuration
        
    Returns:
        An initialized MCP server provider
        
    Raises:
        ValueError: If the provider type is unknown
    """
    from .server.base import MCPServerProvider
    
    logger.info(f"Creating MCP server provider: {provider_type}")
    
    if provider_type == "websocket":
        from .server.providers.websocket import WebSocketServerProvider
        provider = WebSocketServerProvider(**config)
    elif provider_type == "grpc":
        from .server.providers.grpc import GRPCServerProvider
        provider = GRPCServerProvider(**config)
    elif provider_type == "default" or provider_type == "http":
        from .server.providers.http import HTTPServerProvider
        provider = HTTPServerProvider(**config)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    await provider.initialize()
    return provider 