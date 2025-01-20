"""Memory manager for coordinating short-term and long-term memory."""

import logging
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from .short_term import ContextMemory, SessionMemory
from .long_term import StorageMemory, MemoryRetriever
from ..data.vector import VectorIndex, Embeddings
from ..common.errors import PepperpyError
from ..core.lifecycle import Lifecycle
from ..models.types import Message
from .base import BaseMemory, MemoryBackend
from .long_term.retriever import LongTermRetriever
from .long_term.storage import LongTermStorage

logger = logging.getLogger(__name__)

class MemoryError(PepperpyError):
    """Memory error."""
    pass

T = TypeVar("T", bound=BaseMemory)

class MemoryManager(Lifecycle):
    """Memory manager implementation."""
    
    def __init__(
        self,
        name: str,
        backend: MemoryBackend,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize memory manager.
        
        Args:
            name: Manager name
            backend: Memory backend
            config: Optional manager configuration
        """
        super().__init__(name)
        self._backend = backend
        self._config = config or {}
        self._memories: Dict[str, BaseMemory] = {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return manager configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize manager."""
        await self._backend.initialize()
        
    async def _cleanup(self) -> None:
        """Clean up manager."""
        # Clean up memories
        for memory in self._memories.values():
            await memory.cleanup()
            
        # Clean up backend
        await self._backend.cleanup()
        
        # Clear memories
        self._memories.clear()
        
    def get_memory(self, name: str) -> Optional[BaseMemory]:
        """Get memory by name.
        
        Args:
            name: Memory name
            
        Returns:
            Memory instance or None if not found
        """
        return self._memories.get(name)
        
    def create_memory(
        self,
        memory_type: Type[T],
        name: str,
        **kwargs: Any,
    ) -> T:
        """Create memory instance.
        
        Args:
            memory_type: Memory class to create
            name: Memory name
            **kwargs: Additional memory parameters
            
        Returns:
            Memory instance
            
        Raises:
            MemoryError: If memory already exists
        """
        if name in self._memories:
            raise MemoryError(f"Memory '{name}' already exists")
            
        # Create memory
        memory = memory_type(
            name=name,
            backend=self._backend,
            config=self._config.get(name),
            **kwargs,
        )
        
        # Store memory
        self._memories[name] = memory
        
        return memory
        
    def remove_memory(self, name: str) -> None:
        """Remove memory.
        
        Args:
            name: Memory name
            
        Raises:
            MemoryError: If memory does not exist
        """
        if name not in self._memories:
            raise MemoryError(f"Memory '{name}' does not exist")
            
        del self._memories[name]
        
    async def add_message(
        self,
        message: Message,
        memory_names: Optional[List[str]] = None,
    ) -> None:
        """Add message to memories.
        
        Args:
            message: Message to add
            memory_names: Optional list of memory names to add to
            
        Raises:
            MemoryError: If message cannot be added
        """
        try:
            # Get target memories
            memories = (
                [self._memories[name] for name in memory_names]
                if memory_names is not None
                else self._memories.values()
            )
            
            # Add message to memories
            for memory in memories:
                await memory.add_message(message)
                
        except Exception as e:
            raise MemoryError(f"Failed to add message: {e}") from e
            
    async def get_messages(
        self,
        memory_names: Optional[List[str]] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Message]]:
        """Get messages from memories.
        
        Args:
            memory_names: Optional list of memory names to get from
            limit: Optional message limit
            filters: Optional message filters
            
        Returns:
            Dictionary mapping memory names to message lists
            
        Raises:
            MemoryError: If messages cannot be retrieved
        """
        try:
            # Get target memories
            memories = (
                [self._memories[name] for name in memory_names]
                if memory_names is not None
                else self._memories.values()
            )
            
            # Get messages from memories
            results = {}
            for memory in memories:
                messages = await memory.get_messages(
                    limit=limit,
                    filters=filters,
                )
                results[memory.name] = messages
                
            return results
            
        except Exception as e:
            raise MemoryError(f"Failed to get messages: {e}") from e
            
    async def search_messages(
        self,
        query: str,
        memory_names: Optional[List[str]] = None,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
    ) -> Dict[str, List[Tuple[Message, float]]]:
        """Search messages in memories.
        
        Args:
            query: Search query
            memory_names: Optional list of memory names to search in
            limit: Optional result limit
            filters: Optional message filters
            min_score: Minimum relevance score (default: 0.0)
            
        Returns:
            Dictionary mapping memory names to (message, score) lists
            
        Raises:
            MemoryError: If messages cannot be searched
        """
        try:
            # Get target memories
            memories = (
                [self._memories[name] for name in memory_names]
                if memory_names is not None
                else self._memories.values()
            )
            
            # Search messages in memories
            results = {}
            for memory in memories:
                if isinstance(memory, LongTermRetriever):
                    messages = await memory.search(
                        query=query,
                        limit=limit,
                        filters=filters,
                        min_score=min_score,
                    )
                    results[memory.name] = messages
                    
            return results
            
        except Exception as e:
            raise MemoryError(f"Failed to search messages: {e}") from e
            
    async def clear_memories(
        self,
        memory_names: Optional[List[str]] = None,
    ) -> None:
        """Clear memories.
        
        Args:
            memory_names: Optional list of memory names to clear
            
        Raises:
            MemoryError: If memories cannot be cleared
        """
        try:
            # Get target memories
            memories = (
                [self._memories[name] for name in memory_names]
                if memory_names is not None
                else self._memories.values()
            )
            
            # Clear memories
            for memory in memories:
                await memory.clear()
                
        except Exception as e:
            raise MemoryError(f"Failed to clear memories: {e}") from e
            
    def validate(self) -> None:
        """Validate manager state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Manager name cannot be empty")
            
        if not self._backend:
            raise ValueError("Memory backend not provided")
            
        # Validate memories
        for memory in self._memories.values():
            memory.validate()

    def add_context(
        self,
        context_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add context data.
        
        Args:
            context_id: Unique identifier for the context
            data: Context data to store
            metadata: Optional metadata about the context
        """
        self.get_memory(context_id).add_context(context_id, data, metadata)
        
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get context data.
        
        Args:
            context_id: Unique identifier for the context
            
        Returns:
            Context data if found and not expired, None otherwise
        """
        return self.get_memory(context_id).get_context(context_id)
        
    def add_session_entry(
        self,
        session_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add session entry.
        
        Args:
            session_id: Unique identifier for the session
            data: Entry data to store
            metadata: Optional metadata about the entry
        """
        self.get_memory(session_id).add_entry(session_id, data, metadata)
        
    def get_recent_session_entries(
        self,
        session_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent session entries.
        
        Args:
            session_id: Unique identifier for the session
            count: Number of recent entries to return
            
        Returns:
            List of recent entries
        """
        return self.get_memory(session_id).get_recent_entries(session_id, count)
        
    async def store_memory(
        self,
        memory_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None
    ) -> None:
        """Store memory data and optionally index for retrieval.
        
        Args:
            memory_id: Unique identifier for the memory
            data: Memory data to store
            metadata: Optional metadata about the memory
            text: Optional text content for similarity indexing
        """
        self.get_memory(memory_id).store(memory_id, data, metadata)
        if text:
            await self.get_memory(memory_id).index_memory(memory_id, text, metadata)
            
    def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored memory data.
        
        Args:
            memory_id: Unique identifier for the memory
            
        Returns:
            Memory data if found, None otherwise
        """
        return self.get_memory(memory_id).retrieve(memory_id)
        
    async def find_similar_memories(
        self,
        query: str,
        k: int = 5,
        min_similarity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Find memories similar to a query.
        
        Args:
            query: Query text to find similar memories
            k: Number of results to return
            min_similarity: Optional minimum similarity threshold
            
        Returns:
            List of similar memories with metadata and scores
        """
        similar = await self.get_memory(memory_id).retrieve_similar(
            query,
            k=k,
            min_similarity=min_similarity
        )
        
        # Enrich results with full memory data
        results = []
        for item in similar:
            memory = self.get_memory(item["id"]).retrieve(item["id"])
            if memory:
                results.append({
                    **item,
                    "memory": memory
                })
                
        return results 