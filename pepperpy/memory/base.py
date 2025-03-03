"""Base interfaces for the Pepperpy memory system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


class MemoryInterface(ABC, Generic[T]):
    """Base interface for memory management."""

    @abstractmethod
    def store(self, key: str, value: T) -> None:
        """Store a value in memory."""

    @abstractmethod
    def retrieve(self, key: str) -> Optional[T]:
        """Retrieve a value from memory."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value from memory."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all values from memory."""


class ContextualMemory(MemoryInterface[Dict[str, Any]]):
    """Memory system that maintains context between operations."""

    def __init__(self):
        self._context: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []

    def store(self, key: str, value: Dict[str, Any]) -> None:
        """Store context data."""
        self._context[key] = value
        self._history.append({"action": "store", "key": key, "value": value})

    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve context data."""
        return self._context.get(key)

    def delete(self, key: str) -> bool:
        """Delete context data."""
        if key in self._context:
            del self._context[key]
            self._history.append({"action": "delete", "key": key})
            return True
        return False

    def clear(self) -> None:
        """Clear all context data."""
        self._context.clear()
        self._history.append({"action": "clear"})

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the history of memory operations."""
        return self._history.copy()


class VectorMemory(MemoryInterface[Any]):
    """Memory system for vector-based storage and retrieval."""

    def __init__(self, dimension: int):
        self._dimension = dimension
        self._vectors: Dict[str, Any] = {}

    def store(self, key: str, value: Any) -> None:
        """Store a vector."""
        if len(value) != self._dimension:
            raise ValueError(
                f"Vector dimension mismatch. Expected {self._dimension}, got {len(value)}",
            )
        self._vectors[key] = value

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a vector."""
        return self._vectors.get(key)

    def delete(self, key: str) -> bool:
        """Delete a vector."""
        if key in self._vectors:
            del self._vectors[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all vectors."""
        self._vectors.clear()

    def similarity_search(
        self, query_vector: Any, top_k: int = 5,
    ) -> List[tuple[str, float]]:
        """Search for similar vectors."""
        # Implementação básica - em produção, usar uma biblioteca de busca vetorial
        scores = []
        for key, vector in self._vectors.items():
            similarity = self._compute_similarity(query_vector, vector)
            scores.append((key, similarity))

        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]

    def _compute_similarity(self, vec1: Any, vec2: Any) -> float:
        """Compute similarity between two vectors."""
        # Implementação básica - em produção, usar uma biblioteca de álgebra linear
        return sum(a * b for a, b in zip(vec1, vec2))
