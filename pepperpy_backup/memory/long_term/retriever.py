"""Long-term memory retriever implementation."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...common.errors import PepperpyError
from ...models.types import Message
from ..base import BaseMemory, MemoryBackend


class MemoryError(PepperpyError):
    """Memory error."""
    pass


class LongTermRetriever(BaseMemory):
    """Long-term memory retriever implementation."""
    
    def __init__(
        self,
        name: str,
        backend: MemoryBackend,
        namespace: str = "default",
        max_age: Optional[timedelta] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize long-term retriever.
        
        Args:
            name: Memory name
            backend: Memory backend
            namespace: Storage namespace (default: default)
            max_age: Optional maximum age for messages
            config: Optional memory configuration
        """
        super().__init__(name, backend, config)
        self._namespace = namespace
        self._max_age = max_age
        self._metadata_key = f"metadata:{namespace}"
        self._messages_key = f"messages:{namespace}"
        
    @property
    def namespace(self) -> str:
        """Return storage namespace."""
        return self._namespace
        
    async def add_message(self, message: Message) -> None:
        """Add message to memory.
        
        Args:
            message: Message to add
            
        Raises:
            MemoryError: Operation not supported
        """
        raise MemoryError("Retriever is read-only")
        
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
            data = await self._backend.retrieve(self._messages_key)
            if not data:
                return []
                
            # Convert to messages
            messages = [Message.from_dict(msg) for msg in data]
            
            # Filter by age
            if self._max_age is not None:
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
            
    async def search(
        self,
        query: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> List[Tuple[Message, float]]:
        """Search messages by content.
        
        Args:
            query: Search query
            limit: Optional result limit
            filters: Optional message filters
            min_score: Minimum relevance score (default: 0.0)
            
        Returns:
            List of (message, score) tuples
            
        Raises:
            MemoryError: If messages cannot be searched
        """
        try:
            # Get messages
            messages = await self.get_messages(filters=filters)
            if not messages:
                return []
                
            # Calculate relevance scores
            results = []
            for msg in messages:
                score = self._calculate_relevance(query, msg)
                if score >= min_score:
                    results.append((msg, score))
                    
            # Sort by score
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Apply limit
            if limit is not None:
                results = results[:limit]
                
            return results
            
        except Exception as e:
            raise MemoryError(f"Failed to search messages: {e}") from e
            
    async def clear(self) -> None:
        """Clear memory.
        
        Raises:
            MemoryError: Operation not supported
        """
        raise MemoryError("Retriever is read-only")
        
    def _is_expired(self, message: Message, now: datetime) -> bool:
        """Check if message has expired.
        
        Args:
            message: Message to check
            now: Current timestamp
            
        Returns:
            True if message has expired, False otherwise
        """
        if self._max_age is None:
            return False
            
        timestamp = message.metadata.get("stored_at")
        if not timestamp:
            return False
            
        try:
            stored_at = datetime.fromisoformat(timestamp)
            age = now - stored_at
            return age > self._max_age
            
        except (ValueError, TypeError):
            return False
            
    def _calculate_relevance(self, query: str, message: Message) -> float:
        """Calculate relevance score between query and message.
        
        Args:
            query: Search query
            message: Message to score
            
        Returns:
            Relevance score between 0 and 1
        """
        # TODO: Implement proper relevance scoring
        # For now, just check if query appears in content
        return float(query.lower() in message.content.lower())
        
    def validate(self) -> None:
        """Validate memory state."""
        super().validate()
        
        if not self._namespace:
            raise ValueError("Storage namespace cannot be empty")
