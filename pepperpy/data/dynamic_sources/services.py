"""Data service implementations for Pepperpy."""

import logging
from typing import Any, Dict, Optional

from pepperpy.common.services import ServiceError, RESTService, WebSocketService


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
        """Handle REST request."""
        try:
            if method == "GET":
                if path == "/sources":
                    return {"sources": await self.data_manager.get_sources()}
                elif path == "/vectors":
                    return {"vectors": await self.data_manager.get_vectors()}
            elif method == "POST":
                if path == "/ingest":
                    return await self.data_manager.ingest_data(data)
                elif path == "/update":
                    return await self.data_manager.update_data(data)
            
            raise ServiceError(f"Invalid path: {path}")
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            raise ServiceError(str(e))


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
        """Handle WebSocket message."""
        try:
            action = message.get("action")
            if not action:
                raise ServiceError("Missing action")
                
            if action == "subscribe_updates":
                await self.data_manager.subscribe_updates(context)
                return {"status": "subscribed"}
            elif action == "unsubscribe_updates":
                await self.data_manager.unsubscribe_updates(context)
                return {"status": "unsubscribed"}
                
            raise ServiceError(f"Invalid action: {action}")
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            raise ServiceError(str(e)) 