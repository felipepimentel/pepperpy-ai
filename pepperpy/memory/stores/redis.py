"""Redis memory store implementation."""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, TypeVar

import redis.asyncio as redis
from redis.asyncio.client import Redis

from pepperpy.common.errors import MemoryError
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)
from pepperpy.memory.config import RedisConfig
from pepperpy.monitoring.logger import get_logger

T = TypeVar("T", bound=dict[str, Any])
logger = get_logger(__name__)


class RedisMemoryStore(BaseMemoryStore[T]):
    """Redis memory store implementation."""

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis memory store.

        Args:
            config: Redis configuration.
        """
        self.config = config
        self._client: Redis | None = None

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[Redis]:
        """Get Redis client.

        Yields:
            Redis client instance.

        Raises:
            MemoryError: If client is not initialized.
        """
        if not self._client:
            raise MemoryError("Redis client not initialized", store_type="redis")
        try:
            yield self._client
        except Exception as e:
            raise MemoryError(
                "Redis operation failed",
                store_type="redis",
                details={"error": str(e)},
            ) from e

    def _get_key_pattern(self, query: MemoryQuery) -> str:
        """Get Redis key pattern for query.

        Args:
            query: Memory query parameters.

        Returns:
            Redis key pattern.
        """
        return f"{self.config.prefix}:*"

    def _retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve memories from Redis store.

        Args:
            query: Memory query parameters.

        Yields:
            Memory search results matching the query.

        Raises:
            MemoryError: If retrieval fails.
        """

        async def retrieve_generator() -> AsyncIterator[MemorySearchResult[T]]:
            if not self._client:
                raise MemoryError("Redis client not initialized", store_type="redis")

            try:
                pattern = self._get_key_pattern(query)
                async with self._get_client() as client:
                    keys = await self._scan_keys(pattern)

                    for key in keys:
                        entry = await self._load_entry(key, client)
                        if entry is None:
                            continue

                        if not self._matches_filters(entry, query):
                            continue

                        yield MemorySearchResult(
                            entry=entry,
                            score=1.0,
                        )

            except Exception as e:
                raise MemoryError(
                    "Failed to retrieve from Redis",
                    store_type="redis",
                    details={"error": str(e)},
                ) from e

        return retrieve_generator()

    async def _initialize(self) -> None:
        """Initialize Redis client."""
        try:
            # Build Redis URL if not provided
            url = f"redis://{self.config.host}:{self.config.port}/{self.config.db}"
            if self.config.username:
                url = (
                    f"redis://{self.config.username}@"
                    f"{self.config.host}:{self.config.port}/{self.config.db}"
                )
            if self.config.password:
                url = (
                    f"redis://:{self.config.password}@"
                    f"{self.config.host}:{self.config.port}/{self.config.db}"
                )

            # Initialize Redis client with minimal parameters
            self._client = redis.Redis.from_url(
                url,
                decode_responses=True,
                ssl=self.config.ssl,
                ssl_ca_certs=self.config.ssl_ca_certs if self.config.ssl else None,
                ssl_certfile=self.config.ssl_certfile if self.config.ssl else None,
                ssl_keyfile=self.config.ssl_keyfile if self.config.ssl else None,
            )

            # Test connection
            if self._client is None:
                raise RuntimeError("Failed to initialize Redis client")
            await self._client.ping()

        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            raise RuntimeError(f"Failed to initialize Redis client: {e}") from e

    async def _cleanup(self) -> None:
        """Clean up Redis client."""
        if self._client:
            await self._client.close()
            self._client = None

    async def _store(self, entry: MemoryEntry[T]) -> None:
        """Store entry in memory.

        Args:
            entry: Entry to store

        Raises:
            RuntimeError: If storage fails
        """
        if not self._client:
            raise RuntimeError("Redis client not initialized")

        try:
            # Store entry
            data = entry.model_dump()

            if self.config.ttl:
                await self._client.setex(
                    f"{self.config.prefix}:{entry.key}",
                    self.config.ttl,
                    json.dumps(data),
                )
            else:
                await self._client.set(
                    f"{self.config.prefix}:{entry.key}",
                    json.dumps(data),
                )

        except Exception as e:
            logger.error(f"Failed to store in Redis: {e}")
            raise MemoryError(
                "Failed to store in Redis",
                store_type="redis",
                details={"error": str(e)},
            ) from e

    def _matches_filters(
        self,
        entry: MemoryEntry[T],
        query: MemoryQuery,
    ) -> bool:
        """Check if entry matches all query filters.

        Args:
            entry: Memory entry to check
            query: Query containing filters

        Returns:
            bool: True if entry matches all filters
        """
        # Check filters
        if query.filters:
            if "type" in query.filters and entry.type != query.filters["type"]:
                return False
            if "scope" in query.filters and entry.scope != query.filters["scope"]:
                return False

        # Check metadata filter
        if query.metadata:
            if not entry.metadata:
                return False
            if not all(entry.metadata.get(k) == v for k, v in query.metadata.items()):
                return False

        # Check similarity threshold
        similarity = 1.0  # TODO: Implement similarity calculation
        if similarity < query.min_score:
            return False

        return True

    async def _load_entry(
        self,
        key: str,
        client: Redis,
    ) -> MemoryEntry[T] | None:
        """Load and parse a memory entry from Redis.

        Args:
            key: Key to load
            client: Redis client

        Returns:
            MemoryEntry if successful, None if failed
        """
        try:
            data = await client.get(key)
            if not data:
                return None

            entry_data = json.loads(data)
            return MemoryEntry[T].model_validate(entry_data)

        except Exception as e:
            logger.warning(f"Failed to load entry {key}: {e}")
            return None

    async def _scan_keys(
        self,
        pattern: str,
    ) -> list[str]:
        """Scan Redis for keys matching pattern.

        Args:
            pattern: Pattern to match keys against

        Returns:
            List of matching keys

        Raises:
            RuntimeError: If Redis client is not initialized
        """
        if not self._client:
            raise RuntimeError("Redis client not initialized")

        keys = []
        cursor = 0

        while True:
            cursor, matches = await self._client.scan(cursor, pattern)
            keys.extend(matches)
            if cursor == 0:
                break

        return keys

    async def _delete(self, key: str) -> None:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Raises:
            RuntimeError: If deletion fails
        """
        if not self._client:
            raise RuntimeError("Redis client not initialized")

        try:
            await self._client.delete(f"{self.config.prefix}:{key}")
            logger.debug(
                "Deleted memory entry",
                extra={"store": "redis", "key": key},
            )

        except Exception as e:
            logger.error(
                "Failed to delete from Redis",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to delete from Redis: {e}") from e
