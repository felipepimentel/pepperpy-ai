"""
Compatibility layer for existing code using old A2A and MCP imports.

This module provides backward compatibility for code still importing from pepperpy.a2a and pepperpy.mcp.
It should be considered deprecated and new code should use pepperpy.communication directly.
"""

import warnings
from typing import Any

from pepperpy.communication import (
    CommunicationProtocol,
    create_provider,
)


async def create_a2a_provider(provider_type: str = "default", **kwargs: Any) -> Any:
    """
    Create an A2A provider.

    This function maintains backward compatibility with pepperpy.a2a.create_provider.
    New code should use pepperpy.communication.create_provider directly.

    Args:
        provider_type: Type of provider (default, rest, mock, etc.)
        **kwargs: Additional configuration

    Returns:
        A2A provider instance
    """
    warnings.warn(
        "pepperpy.a2a.create_provider is deprecated, use pepperpy.communication.create_provider instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return await create_provider(
        protocol=CommunicationProtocol.A2A, provider_type=provider_type, **kwargs
    )


async def create_mcp_client(client_type: str = "http", **kwargs: Any) -> Any:
    """
    Create an MCP client.

    This function maintains backward compatibility with pepperpy.mcp.create_client.
    New code should use pepperpy.communication.create_provider directly.

    Args:
        client_type: Type of client (http, etc.)
        **kwargs: Additional configuration

    Returns:
        MCP client instance
    """
    warnings.warn(
        "pepperpy.mcp.create_client is deprecated, use pepperpy.communication.create_provider instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return await create_provider(
        protocol=CommunicationProtocol.MCP, provider_type=client_type, **kwargs
    )


async def create_mcp_server(server_type: str = "http", **kwargs: Any) -> Any:
    """
    Create an MCP server.

    This function maintains backward compatibility with pepperpy.mcp.create_server.
    New code should use pepperpy.communication.create_provider directly.

    Args:
        server_type: Type of server (http, etc.)
        **kwargs: Additional configuration

    Returns:
        MCP server instance
    """
    warnings.warn(
        "pepperpy.mcp.create_server is deprecated, use pepperpy.communication.create_provider instead",
        DeprecationWarning,
        stacklevel=2,
    )
    # Note: MCP servers are not fully implemented in the new architecture yet
    return await create_provider(
        protocol=CommunicationProtocol.MCP,
        provider_type=f"server_{server_type}",
        **kwargs,
    )
