"""Cache de vetores para otimização de performance.

Implementa estratégias de cache para vetores e índices,
melhorando a performance de buscas frequentes.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional

from numpy.typing import NDArray


class VectorCache:
    """Cache for vector embeddings."""

    def __init__(self, max_size: int = 10000, ttl: Optional[int] = None) -> None:
        """Initialize vector cache.

        Args:
            max_size: Maximum number of vectors to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._vectors: Dict[str, NDArray] = {}
        self._metadata: Dict[str, datetime] = {}
        self._access_count: Dict[str, int] = {}

    def get(self, key: str) -> Optional[NDArray]:
        """Get vector from cache.

        Args:
            key: Cache key

        Returns:
            Cached vector if found and not expired
        """
        if key not in self._vectors:
            return None

        # Check expiration
        if self.ttl is not None:
            if datetime.now() - self._metadata[key] > timedelta(seconds=self.ttl):
                self._remove(key)
                return None

        # Update access count
        self._access_count[key] += 1
        return self._vectors[key]

    def set(self, key: str, vector: NDArray) -> None:
        """Add vector to cache.

        Args:
            key: Cache key
            vector: Vector to cache
        """
        # Evict if at capacity
        if len(self._vectors) >= self.max_size:
            self._evict()

        self._vectors[key] = vector
        self._metadata[key] = datetime.now()
        self._access_count[key] = 0

    def _remove(self, key: str) -> None:
        """Remove key from cache.

        Args:
            key: Key to remove
        """
        del self._vectors[key]
        del self._metadata[key]
        del self._access_count[key]

    def _evict(self) -> None:
        """Evict least recently used items."""
        # Find least accessed items
        min_count = min(self._access_count.values())
        candidates = {k for k, v in self._access_count.items() if v == min_count}

        # Remove oldest among candidates
        oldest = min(candidates, key=lambda k: self._metadata[k])
        self._remove(oldest)

    def clear(self) -> None:
        """Clear all cached items."""
        self._vectors.clear()
        self._metadata.clear()
        self._access_count.clear()
