"""Vector linker implementation."""

import logging
from typing import Any, Dict, List, Optional, Protocol, TypeVar

import numpy as np
from numpy.typing import NDArray

from ...common.errors import PepperpyError
from ...core.lifecycle import Lifecycle
from ..vector.embeddings import EmbeddingManager
from ..vector.indexer import IndexManager, SearchResult


logger = logging.getLogger(__name__)


class LinkerError(PepperpyError):
    """Linker error."""
    pass


class Source(Protocol):
    """Vector source protocol."""
    
    async def read(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Read data from source.
        
        Args:
            context: Optional read context
            
        Returns:
            Source data
            
        Raises:
            LinkerError: If data cannot be read
        """
        ...


S = TypeVar("S", bound=Source)


class VectorLinker(Lifecycle):
    """Vector linker implementation."""
    
    def __init__(
        self,
        name: str,
        source: Source,
        embedding_manager: EmbeddingManager,
        index_manager: IndexManager,
        min_score: float = 0.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize vector linker.
        
        Args:
            name: Linker name
            source: Data source
            embedding_manager: Embedding manager
            index_manager: Index manager
            min_score: Minimum similarity score (default: 0.0)
            config: Optional linker configuration
        """
        super().__init__(name)
        self._source = source
        self._embedding_manager = embedding_manager
        self._index_manager = index_manager
        self._min_score = min_score
        self._config = config or {}
        
    @property
    def config(self) -> Dict[str, Any]:
        """Return linker configuration."""
        return self._config
        
    async def _initialize(self) -> None:
        """Initialize linker."""
        pass
        
    async def _cleanup(self) -> None:
        """Clean up linker."""
        pass
        
    async def link(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Link query to similar vectors.
        
        Args:
            query: Query text
            k: Number of results (default: 10)
            filters: Optional metadata filters
            context: Optional link context
            
        Returns:
            List of search results
            
        Raises:
            LinkerError: If query cannot be linked
        """
        try:
            # Get query embedding
            embedding = await self._embedding_manager.get_embedding(query)
            
            # Search index
            results = await self._index_manager.search_vectors(
                query=embedding,
                k=k,
                min_score=self._min_score,
                filters=filters,
            )
            
            return results
            
        except Exception as e:
            raise LinkerError(f"Failed to link query: {e}") from e
            
    async def add(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add text to vector index.
        
        Args:
            text: Text to add
            metadata: Optional metadata
            context: Optional add context
            
        Returns:
            Vector ID
            
        Raises:
            LinkerError: If text cannot be added
        """
        try:
            # Get text embedding
            embedding = await self._embedding_manager.get_embedding(text)
            
            # Add to index
            vector_id = await self._index_manager.add_vector(
                vector=embedding,
                metadata=metadata,
            )
            
            return vector_id
            
        except Exception as e:
            raise LinkerError(f"Failed to add text: {e}") from e
            
    async def delete(
        self,
        vector_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Delete vector from index.
        
        Args:
            vector_id: Vector ID
            context: Optional delete context
            
        Returns:
            True if vector was deleted, False if not found
            
        Raises:
            LinkerError: If vector cannot be deleted
        """
        try:
            return await self._index_manager.delete_vector(vector_id)
            
        except Exception as e:
            raise LinkerError(f"Failed to delete vector: {e}") from e
            
    async def update(
        self,
        vector_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update vector in index.
        
        Args:
            vector_id: Vector ID
            text: New text
            metadata: Optional new metadata
            context: Optional update context
            
        Raises:
            LinkerError: If vector cannot be updated
        """
        try:
            # Delete old vector
            if not await self.delete(vector_id, context):
                raise LinkerError(f"Vector {vector_id} not found")
                
            # Add new vector with same ID
            embedding = await self._embedding_manager.get_embedding(text)
            await self._index_manager.add_vector(
                vector=embedding,
                id=vector_id,
                metadata=metadata,
            )
            
        except Exception as e:
            raise LinkerError(f"Failed to update vector: {e}") from e
            
    def validate(self) -> None:
        """Validate linker state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Linker name cannot be empty")
            
        if not self._source:
            raise ValueError("Data source not provided")
            
        if not self._embedding_manager:
            raise ValueError("Embedding manager not provided")
            
        if not self._index_manager:
            raise ValueError("Index manager not provided")
            
        if not 0 <= self._min_score <= 1:
            raise ValueError("Minimum score must be between 0 and 1")
