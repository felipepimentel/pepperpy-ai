"""Redis memory provider implementation."""

from typing import Any, Dict, List, Optional, Union

from pepperpy.memory.providers.base import BaseMemoryProvider


class RedisMemoryProvider(BaseMemoryProvider):
    """Provider implementation for Redis memory storage."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "pepperpy:",
        **kwargs: Any,
    ):
        """Initialize Redis memory provider.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            prefix: Key prefix for Redis keys
            **kwargs: Additional provider options
        """
        super().__init__(**kwargs)
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self._client = None

    @property
    def client(self):
        """Get or create Redis client.

        Returns:
            Redis client
        """
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                )
            except ImportError:
                raise ImportError(
                    "Redis package is required to use RedisMemoryProvider. "
                    "Install it with `pip install redis`."
                )
        return self._client

    def _prefixed_key(self, key: str) -> str:
        """Add prefix to key.

        Args:
            key: Original key

        Returns:
            Prefixed key
        """
        return f"{self.prefix}{key}"

    def store(self, key: str, data: Any) -> None:
        """Store data in Redis.

        Args:
            key: The key to store the data under
            data: The data to store

        Raises:
            ValueError: If storage operation fails
        """
        try:
            import json
            prefixed_key = self._prefixed_key(key)
            serialized = json.dumps(data)
            self.client.set(prefixed_key, serialized)
        except Exception as e:
            raise ValueError(f"Failed to store data in Redis: {e}")

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from Redis.

        Args:
            key: The key to retrieve the data from

        Returns:
            The retrieved data, or None if the key does not exist

        Raises:
            ValueError: If retrieval operation fails
        """
        try:
            import json
            prefixed_key = self._prefixed_key(key)
            data = self.client.get(prefixed_key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            raise ValueError(f"Failed to retrieve data from Redis: {e}")

    def delete(self, key: str) -> bool:
        """Delete data from Redis.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False otherwise

        Raises:
            ValueError: If deletion operation fails
        """
        try:
            prefixed_key = self._prefixed_key(key)
            result = self.client.delete(prefixed_key)
            return result > 0
        except Exception as e:
            raise ValueError(f"Failed to delete data from Redis: {e}")

    def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys in Redis.

        Args:
            pattern: The pattern to filter keys by

        Returns:
            A list of keys

        Raises:
            ValueError: If list operation fails
        """
        try:
            prefixed_pattern = self._prefixed_key(pattern)
            keys = self.client.keys(prefixed_pattern)
            # Remove prefix from keys
            prefix_len = len(self.prefix)
            return [key[prefix_len:] for key in keys]
        except Exception as e:
            raise ValueError(f"Failed to list keys in Redis: {e}")

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            ValueError: If check operation fails
        """
        try:
            prefixed_key = self._prefixed_key(key)
            return bool(self.client.exists(prefixed_key))
        except Exception as e:
            raise ValueError(f"Failed to check key existence in Redis: {e}")
