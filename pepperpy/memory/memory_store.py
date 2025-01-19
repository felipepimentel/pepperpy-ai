"""Base module for memory management with short and long term storage."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json

from pepperpy.memory.conversation import Message


@dataclass
class MemoryEntry:
    """Represents a single memory entry."""
    
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    importance: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_message: Optional[Message] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert memory entry to dictionary format."""
        return {
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "metadata": self.metadata,
            "source_message": self.source_message.to_dict() if self.source_message else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create memory entry from dictionary format."""
        return cls(
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data["importance"],
            metadata=data["metadata"],
            source_message=Message.from_dict(data["source_message"]) if data.get("source_message") else None
        )


class BaseMemoryStore(ABC):
    """Abstract base class for memory stores."""
    
    @abstractmethod
    async def add_memory(self, entry: MemoryEntry) -> None:
        """Add a new memory entry."""
        pass
    
    @abstractmethod
    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_relevance: float = 0.0
    ) -> List[Tuple[MemoryEntry, float]]:
        """Get memories relevant to a query with their relevance scores."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memories."""
        pass


class ShortTermMemory(BaseMemoryStore):
    """In-memory store for short term memories."""
    
    def __init__(
        self,
        max_memories: int = 100,
        importance_threshold: float = 0.5
    ) -> None:
        """Initialize short term memory.
        
        Args:
            max_memories: Maximum number of memories to keep.
            importance_threshold: Minimum importance for long-term storage.
        """
        self.memories: List[MemoryEntry] = []
        self.max_memories = max_memories
        self.importance_threshold = importance_threshold
    
    async def add_memory(self, entry: MemoryEntry) -> None:
        """Add a new memory entry.
        
        Args:
            entry: Memory entry to add.
        """
        self.memories.append(entry)
        
        # Keep only most recent memories
        if len(self.memories) > self.max_memories:
            # Sort by importance and recency
            self.memories.sort(
                key=lambda x: (x.importance, x.timestamp),
                reverse=True
            )
            self.memories = self.memories[:self.max_memories]
    
    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_relevance: float = 0.0
    ) -> List[Tuple[MemoryEntry, float]]:
        """Get memories relevant to a query.
        
        Args:
            query: Query string.
            limit: Maximum number of memories to return.
            min_relevance: Minimum relevance score (0-1).
            
        Returns:
            List of (memory, relevance) tuples.
        """
        # For now, simple recency-based relevance
        # TODO: Implement semantic search
        memories = [
            (mem, 1.0 - (datetime.utcnow() - mem.timestamp).total_seconds() / 86400)
            for mem in self.memories
        ]
        
        # Filter by minimum relevance
        memories = [(mem, score) for mem, score in memories if score >= min_relevance]
        
        # Sort by relevance
        memories.sort(key=lambda x: x[1], reverse=True)
        
        return memories[:limit]
    
    async def clear(self) -> None:
        """Clear all memories."""
        self.memories.clear()


class LongTermMemory(BaseMemoryStore):
    """Persistent store for long term memories."""
    
    def __init__(
        self,
        storage_path: str = "memories.json",
        consolidation_threshold: int = 10
    ) -> None:
        """Initialize long term memory.
        
        Args:
            storage_path: Path to storage file.
            consolidation_threshold: Number of memories before consolidation.
        """
        self.storage_path = storage_path
        self.consolidation_threshold = consolidation_threshold
        self.memories: List[MemoryEntry] = []
        self._load_memories()
    
    def _load_memories(self) -> None:
        """Load memories from storage."""
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.memories = [
                    MemoryEntry.from_dict(entry) for entry in data
                ]
        except FileNotFoundError:
            self.memories = []
    
    def _save_memories(self) -> None:
        """Save memories to storage."""
        with open(self.storage_path, "w") as f:
            json.dump(
                [mem.to_dict() for mem in self.memories],
                f,
                indent=2
            )
    
    async def add_memory(self, entry: MemoryEntry) -> None:
        """Add a new memory entry.
        
        Args:
            entry: Memory entry to add.
        """
        self.memories.append(entry)
        
        # Save to storage
        self._save_memories()
        
        # Consolidate if needed
        if len(self.memories) >= self.consolidation_threshold:
            await self._consolidate_memories()
    
    async def _consolidate_memories(self) -> None:
        """Consolidate similar memories to reduce redundancy."""
        # TODO: Implement memory consolidation
        # Ideas:
        # - Group similar memories
        # - Create summary memories
        # - Remove redundant information
        pass
    
    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        min_relevance: float = 0.0
    ) -> List[Tuple[MemoryEntry, float]]:
        """Get memories relevant to a query.
        
        Args:
            query: Query string.
            limit: Maximum number of memories to return.
            min_relevance: Minimum relevance score (0-1).
            
        Returns:
            List of (memory, relevance) tuples.
        """
        # TODO: Implement semantic search
        # For now, return most important memories
        memories = [
            (mem, mem.importance)
            for mem in self.memories
        ]
        
        # Filter by minimum relevance
        memories = [(mem, score) for mem, score in memories if score >= min_relevance]
        
        # Sort by importance
        memories.sort(key=lambda x: x[1], reverse=True)
        
        return memories[:limit]
    
    async def clear(self) -> None:
        """Clear all memories."""
        self.memories.clear()
        self._save_memories()


class MemoryManager:
    """Manages both short and long term memory stores."""
    
    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        long_term: Optional[LongTermMemory] = None
    ) -> None:
        """Initialize memory manager.
        
        Args:
            short_term: Optional short term memory store.
            long_term: Optional long term memory store.
        """
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()
    
    async def add_memory(
        self,
        content: str,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        source_message: Optional[Message] = None
    ) -> None:
        """Add a new memory.
        
        Args:
            content: Memory content.
            importance: Memory importance (0-1).
            metadata: Optional metadata.
            source_message: Optional source message.
        """
        entry = MemoryEntry(
            content=content,
            importance=importance,
            metadata=metadata or {},
            source_message=source_message
        )
        
        # Add to short term memory
        await self.short_term.add_memory(entry)
        
        # Add to long term if important enough
        if importance >= self.short_term.importance_threshold:
            await self.long_term.add_memory(entry)
    
    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5,
        include_long_term: bool = True
    ) -> List[Tuple[MemoryEntry, float]]:
        """Get memories relevant to a query.
        
        Args:
            query: Query string.
            limit: Maximum total memories to return.
            include_long_term: Whether to include long term memories.
            
        Returns:
            List of (memory, relevance) tuples.
        """
        # Get short term memories
        short_term_limit = limit // 2 if include_long_term else limit
        short_term_memories = await self.short_term.get_relevant_memories(
            query,
            limit=short_term_limit
        )
        
        if not include_long_term:
            return short_term_memories
        
        # Get long term memories
        long_term_memories = await self.long_term.get_relevant_memories(
            query,
            limit=limit - len(short_term_memories)
        )
        
        # Combine and sort by relevance
        all_memories = short_term_memories + long_term_memories
        all_memories.sort(key=lambda x: x[1], reverse=True)
        
        return all_memories[:limit]
    
    async def clear(self) -> None:
        """Clear all memories."""
        await self.short_term.clear()
        await self.long_term.clear() 