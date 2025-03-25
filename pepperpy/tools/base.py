"""Base module for external service integration tools.

This module defines the base interfaces and protocols for all tools
that integrate PepperPy with external services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Set, TypeVar, Union

from pepperpy.core import PepperpyError


class ToolError(PepperpyError):
    """Base error for tool operations."""
    pass


class ConnectionError(ToolError):
    """Error related to external service connection."""
    pass


class AuthenticationError(ToolError):
    """Error related to authentication with external services."""
    pass


class BaseTool(ABC):
    """Base interface for all external service integration tools."""
    
    @abstractmethod
    def capabilities(self) -> Set[str]:
        """Return the capabilities supported by this tool.
        
        Returns:
            Set of capability strings
        """
        pass
    
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