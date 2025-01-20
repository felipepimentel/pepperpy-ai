"""Data service implementations for Pepperpy."""

import logging
from typing import Any, Dict, Optional

from .base import ServiceError, RESTService, WebSocketService


logger = logging.getLogger(__name__)


class DataRESTService(RESTService):
    """Data REST service."""
    
    def __init__(self, data_manager):
        """Initialize service.
        
        Args:
            data_manager: Data manager instance
        """
        self.data_manager = data_manager
        
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
        """
        try:
            if method == "POST":
                if path == "/ingest":
                    return await self.data_manager.ingest(data)
                elif path == "/process":
                    return await self.data_manager.process(data)
                elif path == "/search":
                    return await self.data_manager.search(data)
            elif method == "GET":
                if path == "/status":
                    return {"status": "ok"}
                elif path.startswith("/document/"):
                    doc_id = path.split("/")[-1]
                    return await self.data_manager.get_document(doc_id)
                    
            raise ServiceError(f"Invalid path: {path}")
            
        except Exception as e:
            logger.error(f"Failed to handle request: {str(e)}")
            raise ServiceError(f"Failed to handle request: {str(e)}")


class DataWebSocketService(WebSocketService):
    """Data WebSocket service."""
    
    def __init__(self, data_manager):
        """Initialize service.
        
        Args:
            data_manager: Data manager instance
        """
        self.data_manager = data_manager
        
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
        """
        try:
            action = message.get("action")
            data = message.get("data", {})
            
            if action == "ingest":
                return await self.data_manager.ingest(data)
            elif action == "process":
                return await self.data_manager.process(data)
            elif action == "search":
                return await self.data_manager.search(data)
            else:
                raise ServiceError(f"Invalid action: {action}")
                
        except Exception as e:
            logger.error(f"Failed to handle message: {str(e)}")
            raise ServiceError(f"Failed to handle message: {str(e)}") 