"""Vector cache implementation for the unified caching system.

This module provides specialized caching for vector embeddings with:
- Optimized storage for vector data
- Similarity-based retrieval
- Batch operations
- Metadata support
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

import numpy as np
from numpy.typing import NDArray

from .base import CacheBackend

# Type variable for vector data
VectorT = TypeVar("VectorT", bound=NDArray)


class VectorCache(CacheBackend[NDArray]):
    """Cache for vector embeddings with similarity search."""

    def __init__(
        self,
        max_size: int = 10000,
        cleanup_interval: int = 300,
        similarity_threshold: float = 0.9,
    ):
        """Initialize vector cache.

        Args:
            max_size: Maximum number of vectors to cache
            cleanup_interval: Interval in seconds for expired entry cleanup
            similarity_threshold: Threshold for similarity-based retrieval
        """
        super().__init__()
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._similarity_threshold = similarity_threshold
        self._vectors: Dict[str, NDArray] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._expiration: Dict[str, Optional[datetime]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

        # Start cleanup task
        self._start_cleanup_task()

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        try:
            while True:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_expired()
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            # Log the error but don't crash
            print(f"Error in vector cache cleanup task: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key
                for key, expires_at in self._expiration.items()
                if expires_at is not None and expires_at <= now
            ]

            for key in expired_keys:
                self._remove(key)

    def _remove(self, key: str) -> None:
        """Remove a key from cache.

        Args:
            key: Cache key
        """
        self._vectors.pop(key, None)
        self._metadata.pop(key, None)
        self._timestamps.pop(key, None)
        self._expiration.pop(key, None)

    def _is_expired(self, key: str) -> bool:
        """Check if a key is expired.

        Args:
            key: Cache key

        Returns:
            True if expired, False otherwise
        """
        expires_at = self._expiration.get(key)
        if expires_at is None:
            return False
        return datetime.now() > expires_at

    async def get(self, key: str) -> Optional[NDArray]:
        """Get a vector from cache.

        Args:
            key: Cache key

        Returns:
            Vector if found and not expired, None otherwise
        """
        async with self._lock:
            if key not in self._vectors:
                return None

            if self._is_expired(key):
                self._remove(key)
                return None

            # Update timestamp
            self._timestamps[key] = datetime.now()

            return self._vectors[key]

    async def set(
        self, key: str, value: NDArray, ttl: Optional[Union[int, timedelta]] = None
    ) -> None:
        """Set a vector in cache.

        Args:
            key: Cache key
            value: Vector to cache
            ttl: Optional time-to-live (seconds or timedelta)
        """
        async with self._lock:
            # Check if we need to evict entries
            if key not in self._vectors and len(self._vectors) >= self._max_size:
                await self._evict()

            # Store vector
            self._vectors[key] = value
            self._timestamps[key] = datetime.now()

            # Set expiration
            if ttl is not None:
                if isinstance(ttl, int):
                    ttl = timedelta(seconds=ttl)
                self._expiration[key] = datetime.now() + ttl
            else:
                self._expiration[key] = None

    async def delete(self, key: str) -> bool:
        """Delete a vector from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self._vectors:
                self._remove(key)
                return True
            return False

    async def clear(self) -> None:
        """Clear all vectors from cache."""
        async with self._lock:
            self._vectors.clear()
            self._metadata.clear()
            self._timestamps.clear()
            self._expiration.clear()

    async def contains(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists and not expired, False otherwise
        """
        async with self._lock:
            if key not in self._vectors:
                return False

            if self._is_expired(key):
                self._remove(key)
                return False

            return True

    async def _evict(self) -> None:
        """Evict least recently used vector."""
        if not self._timestamps:
            return

        # Find oldest key
        oldest_key = min(self._timestamps.items(), key=lambda x: x[1])[0]
        self._remove(oldest_key)

    async def set_metadata(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Set metadata for a vector.

        Args:
            key: Cache key
            metadata: Metadata dictionary

        Returns:
            True if metadata was set, False if key not found
        """
        async with self._lock:
            if key not in self._vectors:
                return False

            if self._is_expired(key):
                self._remove(key)
                return False

            self._metadata[key] = metadata
            return True

    async def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a vector.

        Args:
            key: Cache key

        Returns:
            Metadata dictionary if found, None otherwise
        """
        async with self._lock:
            if key not in self._vectors:
                return None

            if self._is_expired(key):
                self._remove(key)
                return None

            return self._metadata.get(key)

    async def find_similar(
        self, vector: NDArray, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find similar vectors in cache.

        Args:
            vector: Query vector
            top_k: Number of results to return

        Returns:
            List of (key, similarity) tuples
        """
        async with self._lock:
            if not self._vectors:
                return []

            # Normalize query vector
            query_norm = np.linalg.norm(vector)
            if query_norm > 0:
                query = vector / query_norm
            else:
                query = vector

            # Calculate similarities
            similarities = []
            for key, vec in self._vectors.items():
                if self._is_expired(key):
                    continue

                # Normalize vector
                vec_norm = np.linalg.norm(vec)
                if vec_norm > 0:
                    normalized = vec / vec_norm
                else:
                    normalized = vec

                # Calculate cosine similarity
                similarity = np.dot(query, normalized)
                similarities.append((key, float(similarity)))

            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Return top-k results
            return similarities[:top_k]

    async def get_similar(
        self, vector: NDArray, threshold: Optional[float] = None
    ) -> Optional[Tuple[str, NDArray]]:
        """Get most similar vector above threshold.

        Args:
            vector: Query vector
            threshold: Similarity threshold (defaults to instance threshold)

        Returns:
            Tuple of (key, vector) if found, None otherwise
        """
        if threshold is None:
            threshold = self._similarity_threshold

        similar = await self.find_similar(vector, top_k=1)
        if not similar:
            return None

        key, similarity = similar[0]
        if similarity < threshold:
            return None

        return key, self._vectors[key]

    async def batch_set(
        self,
        vectors: Dict[str, NDArray],
        ttl: Optional[Union[int, timedelta]] = None,
    ) -> None:
        """Set multiple vectors in cache.

        Args:
            vectors: Dictionary of key-vector pairs
            ttl: Optional time-to-live (seconds or timedelta)
        """
        async with self._lock:
            # Convert TTL to expiration datetime
            expiration = None
            if ttl is not None:
                if isinstance(ttl, int):
                    ttl = timedelta(seconds=ttl)
                expiration = datetime.now() + ttl

            # Check if we need to evict entries
            new_keys = [k for k in vectors if k not in self._vectors]
            if len(self._vectors) + len(new_keys) > self._max_size:
                # Evict enough entries to make room
                to_evict = len(self._vectors) + len(new_keys) - self._max_size
                if to_evict > 0:
                    # Sort by timestamp (oldest first)
                    sorted_keys = sorted(self._timestamps.items(), key=lambda x: x[1])

                    # Evict oldest entries
                    for key, _ in sorted_keys[:to_evict]:
                        self._remove(key)

            # Store vectors
            now = datetime.now()
            for key, vector in vectors.items():
                self._vectors[key] = vector
                self._timestamps[key] = now
                if expiration is not None:
                    self._expiration[key] = expiration
                else:
                    self._expiration[key] = None

    async def batch_get(self, keys: List[str]) -> Dict[str, NDArray]:
        """Get multiple vectors from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-vector pairs for found keys
        """
        async with self._lock:
            result = {}
            now = datetime.now()

            for key in keys:
                if key in self._vectors:
                    # Check expiration
                    expires_at = self._expiration.get(key)
                    if expires_at is not None and expires_at <= now:
                        self._remove(key)
                        continue

                    # Update timestamp
                    self._timestamps[key] = now

                    # Add to result
                    result[key] = self._vectors[key]

            return result

    @property
    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of vectors in cache
        """
        return len(self._vectors)

    def __del__(self) -> None:
        """Clean up resources when object is deleted."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
