"""Context-based short-term memory implementation."""

import json
import logging
from typing import Any, Dict, List, Optional

from ...common.errors import PepperpyError
from ...models.types import Message
from ..base import BaseMemory, MemoryBackend


logger = logging.getLogger(__name__)


class MemoryError(PepperpyError):
    """Memory error."""
    pass


class ContextMemory(BaseMemory):
    """Context-based short-term memory implementation."""
    
    def __init__(
        self,
        name: str,
        backend: MemoryBackend,
        max_messages: int = 100,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize context memory.
        
        Args:
            name: Memory name
            backend: Memory backend
            max_messages: Maximum number of messages to store (default: 100)
            config: Optional memory configuration
        """
        super().__init__(name, backend, config)
        self._max_messages = max_messages
        
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
            
            # Add new message
            messages.append(message)
            
            # Trim messages if needed
            if len(messages) > self._max_messages:
                messages = messages[-self._max_messages:]
                
            # Store messages
            await self._backend.store(
                "messages",
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
            data = await self._backend.retrieve("messages")
            if not data:
                return []
                
            # Convert to messages
            messages = [Message.from_dict(msg) for msg in data]
            
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
            await self._backend.clear()
            
        except Exception as e:
            raise MemoryError(f"Failed to clear memory: {e}") from e
            
    def validate(self) -> None:
        """Validate memory state."""
        super().validate()
        
        if self._max_messages <= 0:
            raise ValueError("Maximum messages must be positive")
