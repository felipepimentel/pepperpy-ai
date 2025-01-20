"""Base vector store classes for Pepperpy."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union, TypeVar

import numpy as np
from numpy.typing import NDArray

from ...common.types import PepperpyObject, DictInitializable, Validatable
from ...common.errors import StorageError, VectorIndexError
from ...core.lifecycle import Lifecycle

T = TypeVar("T")

class VectorStore(Lifecycle, ABC):
    """Base class for vector stores."""
    
    def __init__(
        self,
        name: str,
        dimension: int,
        metric: str = "cosine",
        index_path: Optional[str] = None,
    ) -> None:
        """Initialize vector store.
        
        Args:
            name: Store name
            dimension: Vector dimension
            metric: Distance metric (default: cosine)
            index_path: Optional path to save/load index
        """
        super().__init__(name)
        self._dimension = dimension
        self._metric = metric
        self._index_path = index_path
        self._index: Any = None
        
    @property
    def dimension(self) -> int:
        """Return vector dimension."""
        return self._dimension
        
    @property
    def metric(self) -> str:
        """Return distance metric."""
        return self._metric
        
    @property
    def index_path(self) -> Optional[str]:
        """Return index path."""
        return self._index_path
        
    async def add(self, vectors: NDArray[np.float32], ids: Optional[List[str]] = None) -> List[str]:
        """Add vectors to store.
        
        Args:
            vectors: Vectors to add (shape: [n, dimension])
            ids: Optional vector IDs (if None, generated automatically)
            
        Returns:
            List of vector IDs
            
        Raises:
            VectorIndexError: If vectors have wrong dimension or store is not initialized
        """
        if not self._initialized:
            raise VectorIndexError("Vector store not initialized")
            
        if vectors.shape[1] != self.dimension:
            raise VectorIndexError(f"Expected vectors of dimension {self.dimension}, got {vectors.shape[1]}")
            
        return await self._add(vectors, ids)
        
    @abstractmethod
    async def _add(self, vectors: NDArray[np.float32], ids: Optional[List[str]] = None) -> List[str]:
        """Add vectors implementation."""
        pass
        
    async def search(
        self,
        query: NDArray[np.float32],
        k: int = 10,
        min_similarity: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Search for similar vectors.
        
        Args:
            query: Query vector (shape: [dimension])
            k: Number of results (default: 10)
            min_similarity: Minimum similarity threshold (default: 0.0)
            
        Returns:
            List of (id, similarity) tuples
            
        Raises:
            VectorIndexError: If query has wrong dimension or store is not initialized
        """
        if not self._initialized:
            raise VectorIndexError("Vector store not initialized")
            
        if query.shape[0] != self.dimension:
            raise VectorIndexError(f"Expected query of dimension {self.dimension}, got {query.shape[0]}")
            
        return await self._search(query, k, min_similarity)
        
    @abstractmethod
    async def _search(
        self,
        query: NDArray[np.float32],
        k: int = 10,
        min_similarity: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Search implementation."""
        pass
        
    async def delete(self, ids: List[str]) -> None:
        """Delete vectors from store.
        
        Args:
            ids: Vector IDs to delete
            
        Raises:
            VectorIndexError: If store is not initialized
        """
        if not self._initialized:
            raise VectorIndexError("Vector store not initialized")
            
        await self._delete(ids)
        
    @abstractmethod
    async def _delete(self, ids: List[str]) -> None:
        """Delete implementation."""
        pass
        
    async def clear(self) -> None:
        """Clear all vectors from store.
        
        Raises:
            VectorIndexError: If store is not initialized
        """
        if not self._initialized:
            raise VectorIndexError("Vector store not initialized")
            
        await self._clear()
        
    @abstractmethod
    async def _clear(self) -> None:
        """Clear implementation."""
        pass
        
    async def save(self) -> None:
        """Save index to disk.
        
        Raises:
            VectorIndexError: If store is not initialized or no index path
        """
        if not self._initialized:
            raise VectorIndexError("Vector store not initialized")
            
        if not self._index_path:
            raise VectorIndexError("No index path specified")
            
        await self._save()
        
    @abstractmethod
    async def _save(self) -> None:
        """Save implementation."""
        pass
        
    async def load(self) -> None:
        """Load index from disk.
        
        Raises:
            VectorIndexError: If store is initialized or no index path
        """
        if self._initialized:
            raise VectorIndexError("Vector store already initialized")
            
        if not self._index_path:
            raise VectorIndexError("No index path specified")
            
        await self._load()
        
    @abstractmethod
    async def _load(self) -> None:
        """Load implementation."""
        pass
        
    async def _initialize(self) -> None:
        """Initialize store implementation."""
        if self._index_path:
            await self.load()
            
    async def _cleanup(self) -> None:
        """Cleanup store implementation."""
        if self._index_path:
            await self.save()
            
        self._index = None
        
    def validate(self) -> None:
        """Validate store state."""
        super().validate()
        
        if self.dimension <= 0:
            raise ValueError("Vector dimension must be positive")
            
        if not self.metric:
            raise ValueError("Distance metric cannot be empty") 