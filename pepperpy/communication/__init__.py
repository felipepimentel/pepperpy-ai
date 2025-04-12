"""
Communication module for the PepperPy framework.

This module provides interfaces and factories for communication with external systems,
including agent-to-agent protocols and model communication.
"""

from pepperpy.communication.base import (
    BaseCommunicationProvider,
    CommunicationError,
    CommunicationProtocol,
    CommunicationProvider,
    DataPart,
    FilePart,
    Message,
    MessagePart,
    MessagePartType,
    TextPart,
    create_provider,
)

from .compat import (
    create_a2a_provider,
    create_mcp_client,
    create_mcp_server,
)

__all__ = [
    # Errors
    "CommunicationError",
    # Core interfaces
    "CommunicationProvider",
    "BaseCommunicationProvider",
    # Message types
    "Message",
    "MessagePart",
    "TextPart",
    "DataPart",
    "FilePart",
    "MessagePartType",
    # Protocol types
    "CommunicationProtocol",
    # Factory functions
    "create_provider",
    # Compatibility functions
    "create_a2a_provider",
    "create_mcp_client",
    "create_mcp_server",
]
