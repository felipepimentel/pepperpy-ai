"""Base module for external service integration tools.

This module defines the base interfaces and protocols for all tools
that integrate PepperPy with external services.
"""

from abc import abstractmethod
from typing import Set

from pepperpy.core.base import BaseComponent, PepperpyError


class ToolError(PepperpyError):
    """Base error for tool operations."""

    pass


class ConnectionError(ToolError):
    """Error related to external service connection."""

    pass


class AuthenticationError(ToolError):
    """Error related to authentication with external services."""

    pass


class BaseTool(BaseComponent):
    """Base interface for all external service integration tools."""

    @abstractmethod
    def capabilities(self) -> Set[str]:
        """Return the capabilities supported by this tool.

        Returns:
            Set of capability strings
        """
        pass

    async def _initialize(self) -> None:
        """Initialize the tool by connecting to the external service."""
        await self.connect()

    async def _cleanup(self) -> None:
        """Clean up the tool by disconnecting from the external service."""
        await self.disconnect()

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the external service.

        Returns:
            True if successfully connected, False otherwise

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the external service.

        Returns:
            True if successfully disconnected, False otherwise
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the external service.

        Returns:
            True if connection is working, False otherwise
        """
        pass
