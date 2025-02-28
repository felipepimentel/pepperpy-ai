"""Vector caching for performance optimization.

Implements caching strategies for vectors and indices,
improving performance for frequent searches.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from numpy.typing import NDArray


class EmbeddingCache:
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


class QueryCache:
    """Cache for query results."""

    def __init__(self, max_size: int = 1000, ttl: Optional[int] = 300) -> None:
        """Initialize query cache.

        Args:
            max_size: Maximum number of queries to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._results: Dict[str, List[Dict[str, Any]]] = {}
        self._metadata: Dict[str, datetime] = {}
        self._access_count: Dict[str, int] = {}

    def get(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get results for a query from cache.

        Args:
            query: Query string

        Returns:
            Cached results if found and not expired
        """
        if query not in self._results:
            return None

        # Check expiration
        if self.ttl is not None:
            if datetime.now() - self._metadata[query] > timedelta(seconds=self.ttl):
                self._remove(query)
                return None

        # Update access count
        self._access_count[query] += 1
        return self._results[query]

    def set(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Add query results to cache.

        Args:
            query: Query string
            results: Results to cache
        """
        # Evict if at capacity
        if len(self._results) >= self.max_size:
            self._evict()

        self._results[query] = results
        self._metadata[query] = datetime.now()
        self._access_count[query] = 0

    def _remove(self, query: str) -> None:
        """Remove query from cache.

        Args:
            query: Query to remove
        """
        del self._results[query]
        del self._metadata[query]
        del self._access_count[query]

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
        self._results.clear()
        self._metadata.clear()
        self._access_count.clear()


class ResultCache:
    """Cache for processed results."""

    def __init__(self, max_size: int = 500, ttl: Optional[int] = 600) -> None:
        """Initialize result cache.

        Args:
            max_size: Maximum number of results to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._data: Dict[str, Any] = {}
        self._metadata: Dict[str, datetime] = {}
        self._access_count: Dict[str, int] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get result from cache.

        Args:
            key: Cache key

        Returns:
            Cached result if found and not expired
        """
        if key not in self._data:
            return None

        # Check expiration
        if self.ttl is not None:
            if datetime.now() - self._metadata[key] > timedelta(seconds=self.ttl):
                self._remove(key)
                return None

        # Update access count
        self._access_count[key] += 1
        return self._data[key]

    def set(self, key: str, data: Any) -> None:
        """Add result to cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        # Evict if at capacity
        if len(self._data) >= self.max_size:
            self._evict()

        self._data[key] = data
        self._metadata[key] = datetime.now()
        self._access_count[key] = 0

    def _remove(self, key: str) -> None:
        """Remove key from cache.

        Args:
            key: Key to remove
        """
        del self._data[key]
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
        self._data.clear()
        self._metadata.clear()
        self._access_count.clear()
