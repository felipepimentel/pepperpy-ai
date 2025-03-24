"""Base classes and errors for RAG providers."""

from typing import Any, Dict, List, Optional, Protocol

class RAGError(Exception):
    """Base exception class for RAG errors."""
    pass

class ProviderError(RAGError):
    """Raised when a provider operation fails."""
    pass

class SearchResult:
    """Represents a search result from a RAG provider."""

    def __init__(self, id: str, score: float, metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.score = score
        self.metadata = metadata or {}

class BaseRAGProvider(Protocol):
    """Base protocol for RAG providers."""

    async def initialize(self) -> None:
        """Initialize the provider."""
        ...

    async def store(self, vectors: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """Store vectors in the provider.
        
        Args:
            vectors: List of vectors to store
            batch_size: Number of vectors to process in each batch
        """
        ...

    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of SearchResult objects ordered by similarity
        """
        ...

    async def close(self) -> None:
        """Close the provider and cleanup resources."""
        ...

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration."""
        ...

    def get_capabilities(self) -> Dict[str, bool]:
        """Get the provider capabilities."""
        ... 