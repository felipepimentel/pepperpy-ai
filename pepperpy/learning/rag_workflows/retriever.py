"""Retriever implementation for RAG workflows."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...memory.memory_manager import MemoryManager
from ...common.errors import RAGError
from .pipeline import RetrievalResult

class MemoryRetriever:
    """Retrieves content from memory for RAG workflows."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        min_similarity: float = 0.7
    ):
        """Initialize memory retriever.
        
        Args:
            memory_manager: Memory manager instance
            min_similarity: Minimum similarity threshold
            
        Raises:
            ValueError: If min_similarity is not between 0 and 1
        """
        if not 0 <= min_similarity <= 1:
            raise ValueError("min_similarity must be between 0 and 1")
            
        self.memory_manager = memory_manager
        self.min_similarity = min_similarity
        
    def _matches_filter(self, memory: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """Check if memory matches metadata filter.
        
        Args:
            memory: Memory entry
            filter: Metadata filter
            
        Returns:
            True if memory matches filter
        """
        metadata = memory["memory"]["metadata"]
        return all(
            key in metadata and metadata[key] == value
            for key, value in filter.items()
        )
        
    async def retrieve(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve relevant content from memory.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of retrieval results
            
        Raises:
            RAGError: If retrieval fails
            ValueError: If k is not positive or query is empty
        """
        if k <= 0:
            raise ValueError("k must be positive")
            
        if not query.strip():
            raise ValueError("query cannot be empty")
            
        try:
            # Search memory for similar content
            memories = await self.memory_manager.find_similar_memories(
                query,
                k=k,
                min_similarity=self.min_similarity
            )
            
            # Convert to retrieval results
            results = []
            for memory in memories:
                # Apply filter if provided
                if filter and not self._matches_filter(memory, filter):
                    continue
                    
                try:
                    result = RetrievalResult(
                        content=str(memory["memory"]["data"]),
                        metadata=memory["memory"]["metadata"],
                        score=memory["similarity"],
                        source_id=memory["id"],
                        retrieved_at=datetime.utcnow()
                    )
                    results.append(result)
                except (KeyError, TypeError) as e:
                    # Skip malformed memories but continue processing
                    continue
                    
            return results
            
        except Exception as e:
            raise RAGError(f"Memory retrieval failed: {str(e)}") from e
