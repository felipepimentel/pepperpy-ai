"""Session-based short-term memory implementation."""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...common.errors import PepperpyError
from ...models.types import Message
from ..base import BaseMemory, MemoryBackend


logger = logging.getLogger(__name__)


class MemoryError(PepperpyError):
    """Memory error."""
    pass


class SessionMemory(BaseMemory):
    """Session-based short-term memory implementation."""
    
    def __init__(
        self,
        name: str,
        backend: MemoryBackend,
        session_id: str,
        max_age: Optional[timedelta] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize session memory.
        
        Args:
            name: Memory name
            backend: Memory backend
            session_id: Session identifier
            max_age: Optional maximum age for messages (default: 1 hour)
            config: Optional memory configuration
        """
        super().__init__(name, backend, config)
        self._session_id = session_id
        self._max_age = max_age or timedelta(hours=1)
        
    @property
    def session_id(self) -> str:
        """Return session identifier."""
        return self._session_id
        
    async def add_message(self, message: Message) -> None:
        """Add message to memory.
        
        Args:
            message: Message to add
            
        Raises:
            MemoryError: If message cannot be stored
        """
        try:
            # Get current messages
            messages = await self.get_messages()
            
            # Add timestamp to metadata
            message.metadata["timestamp"] = datetime.utcnow().isoformat()
            
            # Add new message
            messages.append(message)
            
            # Store messages
            await self._backend.store(
                f"messages:{self._session_id}",
                [msg.to_dict() for msg in messages],
            )
            
        except Exception as e:
            raise MemoryError(f"Failed to add message: {e}") from e
            
    async def get_messages(
        self,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Message]:
        """Get messages from memory.
        
        Args:
            limit: Optional message limit
            filters: Optional message filters
            
        Returns:
            List of messages
            
        Raises:
            MemoryError: If messages cannot be retrieved
        """
        try:
            # Get stored messages
            data = await self._backend.retrieve(f"messages:{self._session_id}")
            if not data:
                return []
                
            # Convert to messages
            messages = [Message.from_dict(msg) for msg in data]
            
            # Filter expired messages
            now = datetime.utcnow()
            messages = [
                msg for msg in messages
                if not self._is_expired(msg, now)
            ]
            
            # Apply filters
            if filters:
                messages = [
                    msg for msg in messages
                    if all(
                        msg.metadata.get(k) == v
                        for k, v in filters.items()
                    )
                ]
                
            # Apply limit
            if limit is not None:
                messages = messages[-limit:]
                
            return messages
            
        except Exception as e:
            raise MemoryError(f"Failed to get messages: {e}") from e
            
    async def clear(self) -> None:
        """Clear memory.
        
        Raises:
            MemoryError: If memory cannot be cleared
        """
        try:
            await self._backend.delete(f"messages:{self._session_id}")
            
        except Exception as e:
            raise MemoryError(f"Failed to clear memory: {e}") from e
            
    def _is_expired(self, message: Message, now: datetime) -> bool:
        """Check if message has expired.
        
        Args:
            message: Message to check
            now: Current timestamp
            
        Returns:
            True if message has expired, False otherwise
        """
        timestamp = message.metadata.get("timestamp")
        if not timestamp:
            return False
            
        try:
            created_at = datetime.fromisoformat(timestamp)
            age = now - created_at
            return age > self._max_age
            
        except (ValueError, TypeError):
            return False
            
    def validate(self) -> None:
        """Validate memory state."""
        super().validate()
        
        if not self._session_id:
            raise ValueError("Session ID cannot be empty")
