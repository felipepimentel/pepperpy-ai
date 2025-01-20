"""Base service interfaces for Pepperpy."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from ..common.errors import PepperpyError


class ServiceError(PepperpyError):
    """Service error."""
    pass


@runtime_checkable
class RESTService(Protocol):
    """REST service interface."""
    
    async def handle_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Handle REST request.
        
        Args:
            method: HTTP method
            path: Request path
            data: Optional request data
            headers: Optional request headers
            
        Returns:
            Response data
            
        Raises:
            ServiceError: If request handling fails
            NotImplementedError: If not implemented by concrete class
        """
        raise NotImplementedError


@runtime_checkable
class WebSocketService(Protocol):
    """WebSocket service interface."""
    
    async def handle_message(
        self,
        message: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle WebSocket message.
        
        Args:
            message: Message data
            context: Optional message context
            
        Returns:
            Response data
            
        Raises:
            ServiceError: If message handling fails
            NotImplementedError: If not implemented by concrete class
        """
        raise NotImplementedError 