"""Vector-based memory storage implementation."""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .base import MemoryInterface


class VectorMemory(MemoryInterface[np.ndarray]):
    """Vector-based memory storage implementation."""

    def __init__(self, dimension: int):
        """Initialize vector memory storage.

        Args:
            dimension: Dimension of vectors to store

        """
        self._dimension = dimension
        self._storage: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def store(
        self,
        key: str,
        value: Union[np.ndarray, List[float]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a vector in memory.

        Args:
            key: Key to store vector under
            value: Vector to store (numpy array or list of floats)
            metadata: Optional metadata to store with vector

        Raises:
            ValueError: If vector dimension doesn't match expected dimension

        """
        vector = np.array(value, dtype=np.float32)
        if vector.shape != (self._dimension,):
            raise ValueError(
                f"Vector dimension mismatch. Expected {self._dimension}, "
                f"got {vector.shape[0]}",
            )

        self._storage[key] = vector
        if metadata:
            self._metadata[key] = metadata

    def retrieve(self, key: str) -> Optional[np.ndarray]:
        """Retrieve a vector from memory.

        Args:
            key: Key to retrieve vector for

        Returns:
            Optional[np.ndarray]: Vector if found, None otherwise

        """
        return self._storage.get(key)

    def delete(self, key: str) -> bool:
        """Delete a vector from memory.

        Args:
            key: Key to delete

        Returns:
            bool: True if vector was deleted, False if not found

        """
        if key in self._storage:
            del self._storage[key]
            self._metadata.pop(key, None)
            return True
        return False

    def clear(self) -> None:
        """Clear all vectors from memory."""
        self._storage.clear()
        self._metadata.clear()

    def similarity_search(
        self,
        query: Union[np.ndarray, List[float]],
        top_k: int = 5,
        threshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """Search for similar vectors.

        Args:
            query: Query vector
            top_k: Number of results to return
            threshold: Optional similarity threshold (0 to 1)

        Returns:
            List[Tuple[str, float]]: List of (key, similarity) pairs

        Raises:
            ValueError: If query vector dimension doesn't match expected dimension

        """
        query_vec = np.array(query, dtype=np.float32)
        if query_vec.shape != (self._dimension,):
            raise ValueError(
                f"Query vector dimension mismatch. Expected {self._dimension}, "
                f"got {query_vec.shape[0]}",
            )

        # Normalize query vector
        query_vec = query_vec / np.linalg.norm(query_vec)

        # Calculate cosine similarities
        similarities = []
        for key, vector in self._storage.items():
            # Normalize stored vector
            vector = vector / np.linalg.norm(vector)
            similarity = np.dot(query_vec, vector)

            if threshold is None or similarity >= threshold:
                similarities.append((key, float(similarity)))

        # Sort by similarity (highest first) and take top-k
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a vector.

        Args:
            key: Key to get metadata for

        Returns:
            Optional[Dict[str, Any]]: Metadata if found, None otherwise

        """
        return self._metadata.get(key)

    def update_metadata(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a vector.

        Args:
            key: Key to update metadata for
            metadata: New metadata

        Returns:
            bool: True if metadata was updated, False if key not found

        """
        if key in self._storage:
            if key in self._metadata:
                self._metadata[key].update(metadata)
            else:
                self._metadata[key] = metadata
            return True
        return False

    def list_keys(self) -> List[str]:
        """List all stored keys.

        Returns:
            List[str]: List of stored keys

        """
        return list(self._storage.keys())
