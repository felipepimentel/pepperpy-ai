"""FAISS vector database implementation."""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import faiss
import numpy as np

from pepperpy.common.errors import PepperpyError
from .base import VectorDB, VectorDBError


logger = logging.getLogger(__name__)


class FaissVectorDB(VectorDB):
    """FAISS vector database implementation."""
    
    def __init__(
        self,
        name: str,
        dimension: int,
        index_type: str = "Flat",
        metric: str = "l2",
        path: Optional[Union[str, Path]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize FAISS vector database.
        
        Args:
            name: Database name
            dimension: Vector dimension
            index_type: FAISS index type
            metric: Distance metric (l2 or inner_product)
            path: Optional path to save/load index
            config: Optional database configuration
        """
        super().__init__(name, dimension, config)
        self._index_type = index_type
        self._metric = metric
        self._path = Path(path) if path else None
        self._index: Optional[faiss.Index] = None
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize database."""
        try:
            if self._path and self._path.exists():
                index = faiss.read_index(str(self._path))
                if index.d != self._dimension:
                    raise VectorDBError(
                        f"Index dimension {index.d} does not match "
                        f"expected dimension {self._dimension}"
                    )
                self._index = index
            else:
                self._index = self._create_index()
                
            if self._path:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                metadata_path = self._path.with_suffix(".json")
                if metadata_path.exists():
                    with open(metadata_path) as f:
                        self._metadata = json.load(f)
                
        except Exception as e:
            raise VectorDBError(f"Failed to initialize FAISS index: {e}")
            
    async def cleanup(self) -> None:
        """Clean up database."""
        if self._index and self._path:
            try:
                faiss.write_index(self._index, str(self._path))
                metadata_path = self._path.with_suffix(".json")
                with open(metadata_path, "w") as f:
                    json.dump(self._metadata, f)
            except Exception as e:
                logger.error(f"Failed to save FAISS index: {e}")
                
    def _create_index(self) -> faiss.Index:
        """Create FAISS index.
        
        Returns:
            FAISS index
            
        Raises:
            VectorDBError: If index creation fails
        """
        try:
            if self._metric == "l2":
                index = faiss.IndexFlatL2(self._dimension)
            elif self._metric == "inner_product":
                index = faiss.IndexFlatIP(self._dimension)
            else:
                raise VectorDBError(f"Unsupported metric: {self._metric}")
                
            if self._index_type != "Flat":
                if self._index_type == "IVF":
                    nlist = min(4096, max(self._dimension * 4, 16))
                    quantizer = faiss.IndexFlatL2(self._dimension)
                    index = faiss.IndexIVFFlat(quantizer, self._dimension, nlist)
                    index.train(np.random.randn(nlist * 2, self._dimension).astype(np.float32))
                else:
                    raise VectorDBError(f"Unsupported index type: {self._index_type}")
                    
            return index
            
        except Exception as e:
            raise VectorDBError(f"Failed to create FAISS index: {e}")
            
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
        if not self._index:
            raise VectorDBError("FAISS index not initialized")
            
        try:
            vectors_array = np.array(vectors).astype(np.float32)
            if vectors_array.shape[1] != self._dimension:
                raise VectorDBError(
                    f"Vector dimension {vectors_array.shape[1]} does not match "
                    f"index dimension {self._dimension}"
                )
                
            vector_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            self._index.add(vectors_array)
            
            if metadata:
                for i, vector_id in enumerate(vector_ids):
                    self._metadata[vector_id] = metadata[i]
                    
            return vector_ids
            
        except Exception as e:
            raise VectorDBError(f"Failed to add vectors: {e}")
            
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
        if not self._index:
            raise VectorDBError("FAISS index not initialized")
            
        try:
            query_array = np.array([query_vector]).astype(np.float32)
            if query_array.shape[1] != self._dimension:
                raise VectorDBError(
                    f"Query dimension {query_array.shape[1]} does not match "
                    f"index dimension {self._dimension}"
                )
                
            distances, indices = self._index.search(query_array, k)
            results = []
            
            for i, idx in enumerate(indices[0]):
                if idx == -1:
                    continue
                    
                vector_id = list(self._metadata.keys())[idx]
                metadata = self._metadata.get(vector_id, {})
                
                if filter and not self._matches_filter(metadata, filter):
                    continue
                    
                results.append({
                    "id": vector_id,
                    "distance": float(distances[0][i]),
                    "metadata": metadata,
                })
                
            return results
            
        except Exception as e:
            raise VectorDBError(f"Failed to search vectors: {e}")
            
    def _matches_filter(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        """Check if metadata matches filter.
        
        Args:
            metadata: Vector metadata
            filter: Metadata filter
            
        Returns:
            True if metadata matches filter, False otherwise
        """
        for key, value in filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
        
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
        if not self._index:
            raise VectorDBError("FAISS index not initialized")
            
        try:
            if vector_id not in self._metadata:
                return None
                
            return {
                "id": vector_id,
                "metadata": self._metadata[vector_id],
            }
            
        except Exception as e:
            raise VectorDBError(f"Failed to get vector: {e}")
            
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
        if not self._index:
            raise VectorDBError("FAISS index not initialized")
            
        try:
            for vector_id in vector_ids:
                if vector_id in self._metadata:
                    del self._metadata[vector_id]
                    
        except Exception as e:
            raise VectorDBError(f"Failed to delete vectors: {e}")
            
    async def clear(self) -> None:
        """Clear all vectors.
        
        Raises:
            VectorDBError: If vector deletion fails
        """
        if not self._index:
            raise VectorDBError("FAISS index not initialized")
            
        try:
            self._index.reset()
            self._metadata.clear()
            
        except Exception as e:
            raise VectorDBError(f"Failed to clear vectors: {e}")
            
    def validate(self) -> None:
        """Validate database state."""
        super().validate()
        
        if not self._index_type:
            raise ValueError("FAISS index type cannot be empty")
            
        if not self._metric:
            raise ValueError("Distance metric cannot be empty") 