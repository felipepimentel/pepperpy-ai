"""Core functionality for caching in PepperPy.

This module provides the core functionality for caching in PepperPy,
including memory, disk, and distributed caching.
"""

import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar, Union

from pepperpy.interfaces import AsyncCache, Cache
from pepperpy.utils.logging import get_logger

# Logger for this module
logger = get_logger(__name__)

# Type variable for cache values
T = TypeVar("T")


@dataclass
class CacheKey:
    """Cache key for identifying cached values.

    A cache key is used to identify cached values. It consists of a namespace
    and a key, as well as optional metadata.
    """

    namespace: str
    key: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Get a string representation of the cache key.

        Returns:
            A string representation of the cache key
        """
        return f"{self.namespace}:{self.key}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the cache key to a dictionary.

        Returns:
            The cache key as a dictionary
        """
        return {
            "namespace": self.namespace,
            "key": self.key,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheKey":
        """Create a cache key from a dictionary.

        Args:
            data: The dictionary to create the cache key from

        Returns:
            The created cache key
        """
        return cls(
            namespace=data["namespace"],
            key=data["key"],
            metadata=data.get("metadata", {}),
        )

    def get_full_key(self) -> str:
        """Get the full key as a string.

        Returns:
            The full key as a string
        """
        return f"{self.namespace}:{self.key}"

    def get_hash(self) -> str:
        """Get a hash of the cache key.

        Returns:
            A hash of the cache key
        """
        # Convert the key to a string
        key_str = json.dumps(self.to_dict(), sort_keys=True)

        # Create a hash of the key
        hash_obj = hashlib.sha256(key_str.encode())

        return hash_obj.hexdigest()


@dataclass
class CacheValue(Generic[T]):
    """Cache value for storing cached data.

    A cache value is used to store cached data. It consists of a value, a timestamp,
    and optional metadata.
    """

    value: T
    timestamp: float
    ttl: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self, now: Optional[float] = None) -> bool:
        """Check if the cache value is expired.

        Args:
            now: The current timestamp, or None to use the current time

        Returns:
            True if the cache value is expired, False otherwise
        """
        if self.ttl is None:
            return False

        if now is None:
            now = time.time()

        return now > self.timestamp + self.ttl

    def get_expiry_time(self) -> Optional[float]:
        """Get the expiry time of the cache value.

        Returns:
            The expiry time of the cache value, or None if the value does not expire
        """
        if self.ttl is None:
            return None

        return self.timestamp + self.ttl

    def to_dict(self) -> Dict[str, Any]:
        """Convert the cache value to a dictionary.

        Returns:
            The cache value as a dictionary
        """
        return {
            "value": self.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheValue[Any]":
        """Create a cache value from a dictionary.

        Args:
            data: The dictionary to create the cache value from

        Returns:
            The created cache value
        """
        return cls(
            value=data["value"],
            timestamp=data["timestamp"],
            ttl=data.get("ttl"),
            metadata=data.get("metadata", {}),
        )


class CacheBackend(Generic[T], ABC):
    """Base class for cache backends.

    A cache backend is responsible for storing and retrieving cached data.
    """

    @abstractmethod
    def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        pass

    @abstractmethod
    def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        pass

    @abstractmethod
    def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the cache."""
        pass

    @abstractmethod
    def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        pass

    def _normalize_key(self, key: Union[str, CacheKey]) -> str:
        """Normalize a key to a string.

        Args:
            key: The key to normalize

        Returns:
            The normalized key
        """
        if isinstance(key, CacheKey):
            return key.get_full_key()

        return key


class AsyncCacheBackend(Generic[T], ABC):
    """Base class for asynchronous cache backends.

    An asynchronous cache backend is responsible for storing and retrieving cached data
    asynchronously.
    """

    @abstractmethod
    async def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache asynchronously.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        pass

    @abstractmethod
    async def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache asynchronously.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        pass

    @abstractmethod
    async def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache asynchronously.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the cache asynchronously."""
        pass

    @abstractmethod
    async def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache asynchronously.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        pass

    def _normalize_key(self, key: Union[str, CacheKey]) -> str:
        """Normalize a key to a string.

        Args:
            key: The key to normalize

        Returns:
            The normalized key
        """
        if isinstance(key, CacheKey):
            return key.get_full_key()

        return key


class MemoryCacheBackend(CacheBackend[T]):
    """In-memory cache backend.

    This backend stores cached data in memory.
    """

    def __init__(self):
        """Initialize an in-memory cache backend."""
        self.cache: Dict[str, CacheValue[T]] = {}

    def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        key_str = self._normalize_key(key)

        # Check if the key is in the cache
        if key_str not in self.cache:
            return None

        # Get the cache value
        cache_value = self.cache[key_str]

        # Check if the value is expired
        if cache_value.is_expired():
            # Delete the value
            del self.cache[key_str]

            return None

        # Return the value
        return cache_value.value

    def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        key_str = self._normalize_key(key)

        # Create a cache value
        cache_value = CacheValue(
            value=value,
            timestamp=time.time(),
            ttl=ttl,
        )

        # Set the value in the cache
        self.cache[key_str] = cache_value

    def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        key_str = self._normalize_key(key)

        # Check if the key is in the cache
        if key_str not in self.cache:
            return False

        # Delete the value
        del self.cache[key_str]

        return True

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()

    def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        key_str = self._normalize_key(key)

        # Check if the key is in the cache
        if key_str not in self.cache:
            return False

        # Get the cache value
        cache_value = self.cache[key_str]

        # Check if the value is expired
        if cache_value.is_expired():
            # Delete the value
            del self.cache[key_str]

            return False

        return True


class FileCacheBackend(CacheBackend[T]):
    """File-based cache backend.

    This backend stores cached data in files.
    """

    def __init__(self, directory: str):
        """Initialize a file-based cache backend.

        Args:
            directory: The directory to store the cache files in
        """
        self.directory = Path(directory)

        # Create the directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        key_str = self._normalize_key(key)

        # Get the file path
        file_path = self._get_file_path(key_str)

        # Check if the file exists
        if not file_path.exists():
            return None

        try:
            # Load the cache value
            with open(file_path, "rb") as f:
                cache_value = pickle.load(f)

            # Check if the value is expired
            if cache_value.is_expired():
                # Delete the file
                file_path.unlink()

                return None

            # Return the value
            return cache_value.value
        except Exception as e:
            # Log the error
            logger.error(f"Error loading cache value from {file_path}: {e}")

            # Delete the file
            try:
                file_path.unlink()
            except Exception:
                pass

            return None

    def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        key_str = self._normalize_key(key)

        # Create a cache value
        cache_value = CacheValue(
            value=value,
            timestamp=time.time(),
            ttl=ttl,
        )

        # Get the file path
        file_path = self._get_file_path(key_str)

        try:
            # Save the cache value
            with open(file_path, "wb") as f:
                pickle.dump(cache_value, f)
        except Exception as e:
            # Log the error
            logger.error(f"Error saving cache value to {file_path}: {e}")

    def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        key_str = self._normalize_key(key)

        # Get the file path
        file_path = self._get_file_path(key_str)

        # Check if the file exists
        if not file_path.exists():
            return False

        try:
            # Delete the file
            file_path.unlink()

            return True
        except Exception as e:
            # Log the error
            logger.error(f"Error deleting cache file {file_path}: {e}")

            return False

    def clear(self) -> None:
        """Clear the cache."""
        try:
            # Delete all files in the directory
            for file_path in self.directory.glob("*.cache"):
                try:
                    file_path.unlink()
                except Exception as e:
                    # Log the error
                    logger.error(f"Error deleting cache file {file_path}: {e}")
        except Exception as e:
            # Log the error
            logger.error(f"Error clearing cache directory {self.directory}: {e}")

    def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        key_str = self._normalize_key(key)

        # Get the file path
        file_path = self._get_file_path(key_str)

        # Check if the file exists
        if not file_path.exists():
            return False

        try:
            # Load the cache value
            with open(file_path, "rb") as f:
                cache_value = pickle.load(f)

            # Check if the value is expired
            if cache_value.is_expired():
                # Delete the file
                file_path.unlink()

                return False

            return True
        except Exception as e:
            # Log the error
            logger.error(f"Error loading cache value from {file_path}: {e}")

            # Delete the file
            try:
                file_path.unlink()
            except Exception:
                pass

            return False

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a key.

        Args:
            key: The key to get the file path for

        Returns:
            The file path for the key
        """
        # Create a hash of the key
        hash_obj = hashlib.sha256(key.encode())
        hash_str = hash_obj.hexdigest()

        # Create the file path
        return self.directory / f"{hash_str}.cache"


class NullCacheBackend(CacheBackend[T]):
    """Null cache backend.

    This backend does not cache anything. It is useful for testing or disabling caching.
    """

    def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache.

        Args:
            key: The key to get the value for

        Returns:
            None
        """
        return None

    def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        pass

    def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache.

        Args:
            key: The key to delete the value for

        Returns:
            False
        """
        return False

    def clear(self) -> None:
        """Clear the cache."""
        pass

    def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache.

        Args:
            key: The key to check

        Returns:
            False
        """
        return False


class AsyncMemoryCacheBackend(AsyncCacheBackend[T]):
    """Asynchronous in-memory cache backend.

    This backend stores cached data in memory and provides asynchronous access.
    """

    def __init__(self):
        """Initialize an asynchronous in-memory cache backend."""
        self.cache: Dict[str, CacheValue[T]] = {}

    async def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache asynchronously.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        key_str = self._normalize_key(key)

        # Check if the key is in the cache
        if key_str not in self.cache:
            return None

        # Get the cache value
        cache_value = self.cache[key_str]

        # Check if the value is expired
        if cache_value.is_expired():
            # Delete the value
            del self.cache[key_str]

            return None

        # Return the value
        return cache_value.value

    async def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache asynchronously.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        key_str = self._normalize_key(key)

        # Create a cache value
        cache_value = CacheValue(
            value=value,
            timestamp=time.time(),
            ttl=ttl,
        )

        # Set the value in the cache
        self.cache[key_str] = cache_value

    async def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache asynchronously.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        key_str = self._normalize_key(key)

        # Check if the key is in the cache
        if key_str not in self.cache:
            return False

        # Delete the value
        del self.cache[key_str]

        return True

    async def clear(self) -> None:
        """Clear the cache asynchronously."""
        self.cache.clear()

    async def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache asynchronously.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        key_str = self._normalize_key(key)

        # Check if the key is in the cache
        if key_str not in self.cache:
            return False

        # Get the cache value
        cache_value = self.cache[key_str]

        # Check if the value is expired
        if cache_value.is_expired():
            # Delete the value
            del self.cache[key_str]

            return False

        return True


class AsyncFileCacheBackend(AsyncCacheBackend[T]):
    """Asynchronous file-based cache backend.

    This backend stores cached data in files and provides asynchronous access.
    """

    def __init__(self, directory: str):
        """Initialize an asynchronous file-based cache backend.

        Args:
            directory: The directory to store the cache files in
        """
        self.directory = Path(directory)

        # Create the directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)

    async def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache asynchronously.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        key_str = self._normalize_key(key)

        # Get the file path
        file_path = self._get_file_path(key_str)

        # Check if the file exists
        if not file_path.exists():
            return None

        try:
            # Load the cache value
            with open(file_path, "rb") as f:
                cache_value = pickle.load(f)

            # Check if the value is expired
            if cache_value.is_expired():
                # Delete the file
                file_path.unlink()

                return None

            # Return the value
            return cache_value.value
        except Exception as e:
            # Log the error
            logger.error(f"Error loading cache value from {file_path}: {e}")

            # Delete the file
            try:
                file_path.unlink()
            except Exception:
                pass

            return None

    async def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache asynchronously.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        key_str = self._normalize_key(key)

        # Create a cache value
        cache_value = CacheValue(
            value=value,
            timestamp=time.time(),
            ttl=ttl,
        )

        # Get the file path
        file_path = self._get_file_path(key_str)

        try:
            # Save the cache value
            with open(file_path, "wb") as f:
                pickle.dump(cache_value, f)
        except Exception as e:
            # Log the error
            logger.error(f"Error saving cache value to {file_path}: {e}")

    async def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache asynchronously.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        key_str = self._normalize_key(key)

        # Get the file path
        file_path = self._get_file_path(key_str)

        # Check if the file exists
        if not file_path.exists():
            return False

        try:
            # Delete the file
            file_path.unlink()

            return True
        except Exception as e:
            # Log the error
            logger.error(f"Error deleting cache file {file_path}: {e}")

            return False

    async def clear(self) -> None:
        """Clear the cache asynchronously."""
        try:
            # Delete all files in the directory
            for file_path in self.directory.glob("*.cache"):
                try:
                    file_path.unlink()
                except Exception as e:
                    # Log the error
                    logger.error(f"Error deleting cache file {file_path}: {e}")
        except Exception as e:
            # Log the error
            logger.error(f"Error clearing cache directory {self.directory}: {e}")

    async def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache asynchronously.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        key_str = self._normalize_key(key)

        # Get the file path
        file_path = self._get_file_path(key_str)

        # Check if the file exists
        if not file_path.exists():
            return False

        try:
            # Load the cache value
            with open(file_path, "rb") as f:
                cache_value = pickle.load(f)

            # Check if the value is expired
            if cache_value.is_expired():
                # Delete the file
                file_path.unlink()

                return False

            return True
        except Exception as e:
            # Log the error
            logger.error(f"Error loading cache value from {file_path}: {e}")

            # Delete the file
            try:
                file_path.unlink()
            except Exception:
                pass

            return False

    def _get_file_path(self, key: str) -> Path:
        """Get the file path for a key.

        Args:
            key: The key to get the file path for

        Returns:
            The file path for the key
        """
        # Create a hash of the key
        hash_obj = hashlib.sha256(key.encode())
        hash_str = hash_obj.hexdigest()

        # Create the file path
        return self.directory / f"{hash_str}.cache"


class AsyncNullCacheBackend(AsyncCacheBackend[T]):
    """Asynchronous null cache backend.

    This backend does not cache anything. It is useful for testing or disabling caching.
    """

    async def get(self, key: Union[str, CacheKey]) -> Optional[T]:
        """Get a value from the cache asynchronously.

        Args:
            key: The key to get the value for

        Returns:
            None
        """
        return None

    async def set(
        self, key: Union[str, CacheKey], value: T, ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache asynchronously.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        pass

    async def delete(self, key: Union[str, CacheKey]) -> bool:
        """Delete a value from the cache asynchronously.

        Args:
            key: The key to delete the value for

        Returns:
            False
        """
        return False

    async def clear(self) -> None:
        """Clear the cache asynchronously."""
        pass

    async def has(self, key: Union[str, CacheKey]) -> bool:
        """Check if a key is in the cache asynchronously.

        Args:
            key: The key to check

        Returns:
            False
        """
        return False


# Use separate type variables for the manager classes to avoid conflicts
S = TypeVar("S")
R = TypeVar("R")


class CacheManager(Cache[S]):
    """Cache manager.

    The cache manager provides a unified interface for working with different
    cache backends.
    """

    def __init__(self, backend: Optional[CacheBackend[S]] = None):
        """Initialize a cache manager.

        Args:
            backend: The cache backend to use, or None to use an in-memory backend
        """
        self.backend = backend or MemoryCacheBackend[S]()

    def get(self, key: str) -> Optional[S]:
        """Get a value from the cache.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        return self.backend.get(key)

    def set(self, key: str, value: S, ttl: Optional[int] = None) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        self.backend.set(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Delete a value from the cache.

        Args:
            key: The key to delete the value for

        Returns:
            True if the key was deleted, False otherwise
        """
        return self.backend.delete(key)

    def clear(self) -> None:
        """Clear the cache."""
        self.backend.clear()

    def has(self, key: str) -> bool:
        """Check if a key is in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        return self.backend.has(key)


class AsyncCacheManager(AsyncCache[R]):
    """Asynchronous cache manager.

    The asynchronous cache manager provides a unified interface for working with
    different asynchronous cache backends.
    """

    def __init__(self, backend: Optional[AsyncCacheBackend[R]] = None):
        """Initialize an asynchronous cache manager.

        Args:
            backend: The cache backend to use, or None to use an in-memory backend
        """
        self.backend = backend or AsyncMemoryCacheBackend[R]()

    async def aget(self, key: str) -> Optional[R]:
        """Get a value from the cache asynchronously.

        Args:
            key: The key to get the value for

        Returns:
            The value, or None if the key is not in the cache or the value is expired
        """
        return await self.backend.get(key)

    async def aset(self, key: str, value: R, ttl: Optional[int] = None) -> None:
        """Set a value in the cache asynchronously.

        Args:
            key: The key to set the value for
            value: The value to set
            ttl: The time-to-live in seconds, or None for no expiration
        """
        await self.backend.set(key, value, ttl)

    async def adelete(self, key: str) -> None:
        """Delete a value from the cache asynchronously.

        Args:
            key: The key to delete the value for
        """
        await self.backend.delete(key)

    async def aclear(self) -> None:
        """Clear the cache asynchronously."""
        await self.backend.clear()

    async def ahas(self, key: str) -> bool:
        """Check if a key is in the cache asynchronously.

        Args:
            key: The key to check

        Returns:
            True if the key is in the cache, False otherwise
        """
        return await self.backend.has(key)


# Create a global cache manager
_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager.

    Returns:
        The global cache manager
    """
    return _cache_manager


# Create a global asynchronous cache manager
_async_cache_manager = AsyncCacheManager()


def get_async_cache_manager() -> AsyncCacheManager:
    """Get the global asynchronous cache manager.

    Returns:
        The global asynchronous cache manager
    """
    return _async_cache_manager
