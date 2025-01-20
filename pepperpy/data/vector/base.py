"""Base vector database implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pepperpy.common.errors import PepperpyError
from pepperpy.core.lifecycle import Lifecycle


class VectorDBError(PepperpyError):
    """Vector database error."""
    pass


class VectorDB(Lifecycle, ABC):
    """Base class for vector databases."""
    
    def __init__(
        self,
        name: str,
        dimension: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize vector database.
        
        Args:
            name: Database name
            dimension: Vector dimension
            config: Optional database configuration
        """
        super().__init__()
        self.name = name
        self._dimension = dimension
        self._config = config or {}
        
    @property
    def dimension(self) -> int:
        """Get vector dimension."""
        return self._dimension
        
    @property
    def config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self._config
        
    @abstractmethod
    async def add_vectors(
        self,
        vectors: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Add vectors to database.
        
        Args:
            vectors: List of vectors to add
            metadata: Optional metadata for each vector
            
        Returns:
            List of vector IDs
            
        Raises:
            VectorDBError: If vector addition fails
        """
        pass
        
    @abstractmethod
    async def search_vectors(
        self,
        query_vector: List[float],
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors.
        
        Args:
            query_vector: Vector to search for
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of similar vectors with metadata
            
        Raises:
            VectorDBError: If vector search fails
        """
        pass
        
    @abstractmethod
    async def get_vector(
        self,
        vector_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get vector by ID.
        
        Args:
            vector_id: Vector ID
            
        Returns:
            Vector with metadata if found, None otherwise
            
        Raises:
            VectorDBError: If vector retrieval fails
        """
        pass
        
    @abstractmethod
    async def delete_vectors(
        self,
        vector_ids: List[str],
    ) -> None:
        """Delete vectors by ID.
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Raises:
            VectorDBError: If vector deletion fails
        """
        pass
        
    @abstractmethod
    async def clear(self) -> None:
        """Clear all vectors.
        
        Raises:
            VectorDBError: If vector deletion fails
        """
        pass
        
    def validate(self) -> None:
        """Validate database state."""
        super().validate()
        
        if not self.name:
            raise ValueError("Database name cannot be empty")
            
        if self._dimension <= 0:
            raise ValueError("Vector dimension must be positive") 