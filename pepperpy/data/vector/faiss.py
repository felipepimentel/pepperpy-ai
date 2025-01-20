"""FAISS vector store implementation for Pepperpy."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import faiss
from numpy.typing import NDArray

from ...common.errors import VectorIndexError
from .base import VectorStore

logger = logging.getLogger(__name__)

class FAISSVectorStore(VectorStore):
    """FAISS vector store implementation."""
    
    def __init__(
        self,
        name: str,
        dimension: int,
        metric: str = "cosine",
        index_path: Optional[str] = None,
        index_type: str = "Flat",
    ) -> None:
        """Initialize FAISS vector store.
        
        Args:
            name: Store name
            dimension: Vector dimension
            metric: Distance metric (default: cosine)
            index_path: Optional path to save/load index
            index_type: FAISS index type (default: Flat)
        """
        super().__init__(name, dimension, metric, index_path)
        self._index_type = index_type
        self._id_map: Dict[str, int] = {}
        self._next_id = 0
        
    async def _initialize(self) -> None:
        """Initialize FAISS index."""
        await super()._initialize()
        
        if not self._initialized:
            # Create FAISS index
            if self._metric == "cosine":
                self._index = faiss.IndexFlatIP(self.dimension)
            elif self._metric == "euclidean":
                self._index = faiss.IndexFlatL2(self.dimension)
            else:
                raise VectorIndexError(f"Unsupported metric: {self._metric}")
                
            logger.debug(f"Created FAISS index of type {self._index_type}")
            
    async def _add(self, vectors: NDArray[np.float32], ids: Optional[List[str]] = None) -> List[str]:
        """Add vectors to FAISS index."""
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            
        # Map string IDs to integer indices
        for id_ in ids:
            self._id_map[id_] = self._next_id
            self._next_id += 1
            
        # Add vectors to index
        self._index.add(vectors)
        logger.debug(f"Added {len(vectors)} vectors to FAISS index")
        
        return ids
        
    async def _search(
        self,
        query: NDArray[np.float32],
        k: int = 10,
        min_similarity: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Search FAISS index."""
        # Reshape query to 2D array
        query = query.reshape(1, -1)
        
        # Search index
        distances, indices = self._index.search(query, k)
        
        # Convert results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            # Skip invalid indices
            if idx == -1:
                continue
                
            # Convert distance to similarity
            if self._metric == "cosine":
                similarity = float(distance)
            else:
                similarity = 1.0 / (1.0 + float(distance))
                
            # Apply similarity threshold
            if similarity < min_similarity:
                continue
                
            # Find string ID for index
            id_ = next(k for k, v in self._id_map.items() if v == idx)
            results.append((id_, similarity))
            
        return results
        
    async def _delete(self, ids: List[str]) -> None:
        """Delete vectors from FAISS index."""
        # FAISS doesn't support deletion, so we need to rebuild the index
        raise NotImplementedError("Deletion not supported by FAISS")
        
    async def _clear(self) -> None:
        """Clear FAISS index."""
        # Reset index
        await self._initialize()
        self._id_map.clear()
        self._next_id = 0
        
    async def _save(self) -> None:
        """Save FAISS index to disk."""
        # Create parent directory if needed
        path = Path(self._index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save index
        faiss.write_index(self._index, str(path))
        logger.debug(f"Saved FAISS index to {path}")
        
    async def _load(self) -> None:
        """Load FAISS index from disk."""
        path = Path(self._index_path)
        if not path.exists():
            raise VectorIndexError(f"Index file not found: {path}")
            
        # Load index
        self._index = faiss.read_index(str(path))
        logger.debug(f"Loaded FAISS index from {path}")
        
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"dimension={self.dimension}, "
            f"metric={self.metric}, "
            f"index_type={self._index_type}, "
            f"vectors={len(self._id_map)}"
            f")"
        ) 