"""Vector data module for Pepperpy framework."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from numpy.typing import NDArray

from pepperpy.core.utils.errors import PepperpyError


class VectorError(PepperpyError):
    """Vector error class."""
    pass


@dataclass
class Embeddings:
    """Represents embeddings for a piece of text."""
    
    text: str
    vector: NDArray[np.float32]
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    
    def __post_init__(self):
        """Validate embeddings after initialization."""
        if not self.text:
            raise VectorError("Text cannot be empty")
        
        if not isinstance(self.vector, np.ndarray):
            raise VectorError("Vector must be a numpy array")
        
        if self.vector.dtype != np.float32:
            raise VectorError("Vector must be float32")
        
        if not isinstance(self.metadata, dict):
            raise VectorError("Metadata must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert embeddings to dictionary.
        
        Returns:
            Dictionary representation of embeddings
        """
        return {
            "id": str(self.id),
            "text": self.text,
            "vector": self.vector.tolist(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Embeddings":
        """Create embeddings from dictionary.
        
        Args:
            data: Dictionary representation of embeddings
            
        Returns:
            Embeddings instance
            
        Raises:
            VectorError: If data is invalid
        """
        if not isinstance(data, dict):
            raise VectorError("Data must be a dictionary")
        
        required_fields = {"id", "text", "vector"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            raise VectorError(f"Missing required fields: {missing_fields}")
        
        return cls(
            text=data["text"],
            vector=np.array(data["vector"], dtype=np.float32),
            metadata=data.get("metadata", {}),
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
        )


class VectorIndex:
    """Vector index for efficient similarity search."""
    
    def __init__(self, dimension: int, metric: str = "cosine"):
        """Initialize vector index.
        
        Args:
            dimension: Vector dimension
            metric: Distance metric (cosine, euclidean, or dot)
        """
        self.dimension = dimension
        self.metric = metric
        self._vectors: List[NDArray[np.float32]] = []
        self._embeddings: List[Embeddings] = []
        self._is_initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if index is initialized."""
        return self._is_initialized
    
    def initialize(self) -> None:
        """Initialize index."""
        if self.is_initialized:
            return
        
        if self.metric not in {"cosine", "euclidean", "dot"}:
            raise VectorError(f"Unsupported metric: {self.metric}")
        
        self._is_initialized = True
    
    def add(self, embeddings: Embeddings) -> None:
        """Add embeddings to index.
        
        Args:
            embeddings: Embeddings to add
            
        Raises:
            VectorError: If adding fails
        """
        if not self.is_initialized:
            raise VectorError("Index not initialized")
        
        if embeddings.vector.shape != (self.dimension,):
            raise VectorError(
                f"Vector dimension mismatch: {embeddings.vector.shape} != ({self.dimension},)"
            )
        
        self._vectors.append(embeddings.vector)
        self._embeddings.append(embeddings)
    
    def search(
        self,
        query: NDArray[np.float32],
        k: int = 10,
    ) -> List[Tuple[Embeddings, float]]:
        """Search for similar vectors.
        
        Args:
            query: Query vector
            k: Number of results to return
            
        Returns:
            List of (embeddings, score) tuples
            
        Raises:
            VectorError: If search fails
        """
        if not self.is_initialized:
            raise VectorError("Index not initialized")
        
        if query.shape != (self.dimension,):
            raise VectorError(
                f"Query dimension mismatch: {query.shape} != ({self.dimension},)"
            )
        
        if not self._vectors:
            return []
        
        # Convert list of vectors to matrix
        matrix = np.stack(self._vectors)
        
        # Calculate distances
        if self.metric == "cosine":
            # Normalize vectors
            matrix_norm = np.linalg.norm(matrix, axis=1, keepdims=True)
            query_norm = np.linalg.norm(query)
            
            # Calculate cosine similarity
            scores = np.dot(matrix / matrix_norm, query / query_norm).flatten()
            
        elif self.metric == "euclidean":
            # Calculate euclidean distance
            scores = -np.linalg.norm(matrix - query, axis=1)
            
        else:  # dot product
            # Calculate dot product
            scores = np.dot(matrix, query).flatten()
        
        # Get top k indices
        top_k = np.argsort(scores)[-k:][::-1]
        
        # Return results
        return [
            (self._embeddings[i], float(scores[i]))
            for i in top_k
        ]
    
    def clear(self) -> None:
        """Clear index."""
        self._vectors.clear()
        self._embeddings.clear()
    
    def __len__(self) -> int:
        """Get number of vectors in index."""
        return len(self._vectors) 