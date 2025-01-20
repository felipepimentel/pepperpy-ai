"""Learning service implementations for Pepperpy."""

import logging
from typing import Any, Dict, Optional

from .base import ServiceError, RESTService, WebSocketService


logger = logging.getLogger(__name__)


class LearningRESTService(RESTService):
    """Learning REST service."""
    
    def __init__(self, learning_manager):
        """Initialize service.
        
        Args:
            learning_manager: Learning manager instance
        """
        self.learning_manager = learning_manager
        
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
                if path == "/train":
                    return await self.learning_manager.train(data)
                elif path == "/evaluate":
                    return await self.learning_manager.evaluate(data)
            elif method == "GET":
                if path == "/status":
                    return {"status": "ok"}
                    
            raise ServiceError(f"Invalid path: {path}")
            
        except Exception as e:
            logger.error(f"Failed to handle request: {str(e)}")
            raise ServiceError(f"Failed to handle request: {str(e)}")


class LearningWebSocketService(WebSocketService):
    """Learning WebSocket service."""
    
    def __init__(self, learning_manager):
        """Initialize service.
        
        Args:
            learning_manager: Learning manager instance
        """
        self.learning_manager = learning_manager
        
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
            
            if action == "train":
                return await self.learning_manager.train(data)
            elif action == "evaluate":
                return await self.learning_manager.evaluate(data)
            else:
                raise ServiceError(f"Invalid action: {action}")
                
        except Exception as e:
            logger.error(f"Failed to handle message: {str(e)}")
            raise ServiceError(f"Failed to handle message: {str(e)}") 