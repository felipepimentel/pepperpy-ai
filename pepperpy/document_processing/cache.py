"""Document processing cache module.

This module provides caching mechanisms for document processing to avoid
reprocessing the same document multiple times.
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pepperpy.core.base import PepperpyError


class DocumentCacheError(PepperpyError):
    """Error raised by document cache operations."""

    pass


class DocumentCache:
    """Cache for document processing results.

    This class provides a simple file-based cache for storing document
    processing results to avoid reprocessing the same document multiple times.
    """

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        max_age: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize document cache.

        Args:
            cache_dir: Directory to store cache files, defaults to .pepperpy/cache/documents
            max_age: Maximum age of cache entries in seconds, defaults to 7 days
            **kwargs: Additional configuration options
        """
        # Set cache directory
        if cache_dir is None:
            home_dir = Path.home()
            cache_dir = home_dir / ".pepperpy" / "cache" / "documents"
        elif isinstance(cache_dir, str):
            cache_dir = Path(cache_dir)

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set max age (default to 7 days)
        self.max_age = max_age or 7 * 24 * 60 * 60  # 7 days in seconds

        # Cache statistics
        self.hits = 0
        self.misses = 0

    def get_cache_key(
        self,
        file_path: Union[str, Path],
        provider_name: str,
        operation: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a cache key for a document operation.

        Args:
            file_path: Path to document
            provider_name: Name of the provider
            operation: Operation name (e.g., 'extract_text', 'extract_metadata')
            options: Additional operation options that affect the result

        Returns:
            Cache key string
        """
        # Convert file_path to Path
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Get file modification time and size
        if not file_path.exists():
            raise DocumentCacheError(f"File not found: {file_path}")

        stat = file_path.stat()
        mtime = stat.st_mtime
        size = stat.st_size

        # Prepare data for hash
        data = {
            "path": str(file_path.absolute()),
            "mtime": mtime,
            "size": size,
            "provider": provider_name,
            "operation": operation,
            "options": options or {},
        }

        # Create JSON string of data and hash it
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file for the given key.

        Args:
            cache_key: Cache key string

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def exists(self, cache_key: str) -> bool:
        """Check if cache entry exists and is valid.

        Args:
            cache_key: Cache key string

        Returns:
            True if cache entry exists and is not expired
        """
        cache_path = self.get_cache_path(cache_key)

        # Check if file exists
        if not cache_path.exists():
            return False

        # Check if file is expired
        stat = cache_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        now = datetime.now()

        if now - mtime > timedelta(seconds=self.max_age):
            # Cache is expired, remove it
            try:
                os.remove(cache_path)
            except OSError:
                # Ignore errors on cache removal
                pass
            return False

        return True

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cache entry for the given key.

        Args:
            cache_key: Cache key string

        Returns:
            Cache entry dict or None if not found or expired
        """
        if not self.exists(cache_key):
            self.misses += 1
            return None

        try:
            cache_path = self.get_cache_path(cache_key)
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.hits += 1
            return data
        except (OSError, json.JSONDecodeError):
            # If there's an error reading cache, treat as cache miss
            self.misses += 1
            return None

    def set(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Set cache entry for the given key.

        Args:
            cache_key: Cache key string
            data: Data to store in cache

        Returns:
            True if cache entry was set successfully
        """
        try:
            cache_path = self.get_cache_path(cache_key)

            # Add timestamp to data
            data_with_meta = {"timestamp": datetime.now().isoformat(), "data": data}

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data_with_meta, f, ensure_ascii=False, indent=2)

            return True
        except OSError:
            # If there's an error writing cache, log and continue
            return False

    def invalidate(self, cache_key: str) -> bool:
        """Invalidate cache entry for the given key.

        Args:
            cache_key: Cache key string

        Returns:
            True if cache entry was invalidated successfully
        """
        try:
            cache_path = self.get_cache_path(cache_key)
            if cache_path.exists():
                os.remove(cache_path)
            return True
        except OSError:
            return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                os.remove(cache_file)
                count += 1
            except OSError:
                # Ignore errors on cache removal
                pass

        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        # Count cache files
        cache_files = list(self.cache_dir.glob("*.json"))
        cache_size = sum(f.stat().st_size for f in cache_files)

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": self.hits / (self.hits + self.misses)
            if (self.hits + self.misses) > 0
            else 0,
            "entries": len(cache_files),
            "size_bytes": cache_size,
        }


# Global cache instance
_cache: Optional[DocumentCache] = None


def get_document_cache(
    cache_dir: Optional[Union[str, Path]] = None,
    max_age: Optional[int] = None,
    **kwargs: Any,
) -> DocumentCache:
    """Get document cache instance.

    Args:
        cache_dir: Directory to store cache files
        max_age: Maximum age of cache entries in seconds
        **kwargs: Additional configuration options

    Returns:
        Document cache instance
    """
    global _cache

    if _cache is None:
        _cache = DocumentCache(cache_dir=cache_dir, max_age=max_age, **kwargs)

    return _cache
