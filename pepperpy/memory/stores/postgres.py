"""PostgreSQL memory store implementation."""

import json
from collections.abc import AsyncIterator
from typing import Any

import asyncpg
from asyncpg.pool import Pool

from pepperpy.memory.store import BaseMemoryStore
from pepperpy.memory.store_config import PostgresConfig
from pepperpy.memory.types import (
    MemoryEntry,
    MemoryQuery,
    MemoryResult,
    MemoryScope,
)
from pepperpy.monitoring.logger import get_logger

_logger = get_logger(__name__)


class PostgresMemoryStore(BaseMemoryStore[dict[str, Any]]):
    """PostgreSQL memory store implementation."""

    def __init__(self, config: PostgresConfig) -> None:
        """Initialize store.

        Args:
            config: Store configuration
        """
        super().__init__()
        self.config = config
        self._pool: Pool | None = None

    @property
    def pool(self) -> Pool:
        """Get the connection pool.

        Returns:
            The connection pool.

        Raises:
            RuntimeError: If pool is not initialized.
        """
        if self._pool is None:
            raise RuntimeError("PostgreSQL pool not initialized")
        return self._pool

    @pool.setter
    def pool(self, value: Pool | None) -> None:
        """Set the connection pool.

        Args:
            value: The connection pool.
        """
        self._pool = value

    async def initialize(self) -> None:
        """Initialize the store.

        Raises:
            RuntimeError: If initialization fails
        """
        try:
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
            )

            # Create schema and table if they don't exist
            async with self.pool.acquire() as conn:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema}")
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS
                    {self.config.schema}.{self.config.table} (
                        key TEXT PRIMARY KEY,
                        content JSONB NOT NULL,
                        scope TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb
                    )
                    """
                )

            _logger.info(
                "Initialized PostgreSQL store",
                extra={"schema": self.config.schema, "table": self.config.table},
            )
        except Exception as e:
            _logger.error(
                "Failed to initialize PostgreSQL store",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to initialize PostgreSQL store: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources.

        Raises:
            RuntimeError: If cleanup fails
        """
        try:
            if self._pool:
                await self._pool.close()
                self._pool = None
                _logger.info("Cleaned up PostgreSQL store")
        except Exception as e:
            _logger.error(
                "Failed to clean up PostgreSQL store",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to clean up PostgreSQL store: {e}") from e

    async def _store_impl(
        self,
        key: str,
        value: dict[str, Any],
        scope: MemoryScope,
        metadata: dict[str, str] | None,
    ) -> MemoryEntry[dict[str, Any]]:
        """Store data in memory.

        Args:
            key: Key to store under
            value: Value to store
            scope: Storage scope
            metadata: Optional metadata

        Returns:
            Created memory entry

        Raises:
            RuntimeError: If storage fails
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.config.schema}.{self.config.table}
                    (key, content, scope, metadata)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (key) DO UPDATE
                    SET content = $2, scope = $3, metadata = $4
                    """,
                    key,
                    json.dumps(value),
                    scope.value,
                    json.dumps(metadata or {}),
                )

            # Create and return entry
            entry = MemoryEntry(
                key=key,
                value=value,
                scope=scope,
                metadata=metadata or {},
            )

            _logger.debug(
                "Stored memory entry",
                extra={"store": "postgres", "key": key},
            )
            return entry

        except Exception as e:
            _logger.error(
                "Failed to store in PostgreSQL",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to store in PostgreSQL: {e}") from e

    def _retrieve_impl(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemoryResult[dict[str, Any]]]:
        """Retrieve memory entries.

        Args:
            query: Query parameters

        Returns:
            Iterator of memory results

        Raises:
            RuntimeError: If retrieval fails
        """

        async def retrieve_generator() -> AsyncIterator[MemoryResult[dict[str, Any]]]:
            try:
                # Build query
                sql = f"""
                    SELECT key, content, scope, metadata
                    FROM {self.config.schema}.{self.config.table}
                    WHERE 1=1
                """
                params: list[Any] = []

                # Add scope filter
                if query.scope:
                    sql += " AND scope = $1"
                    params.append(query.scope.value)

                # Add metadata filter
                if query.metadata_filter:
                    for i, (key, value) in enumerate(query.metadata_filter.items()):
                        param_idx = i * 2 + len(params)
                        sql += f" AND metadata->>${param_idx + 1} = ${param_idx + 2}"
                        params.extend([key, json.dumps(value)])

                # Add limit
                if query.limit:
                    sql += f" LIMIT ${len(params) + 1}"
                    params.append(query.limit)

                # Execute query
                async with self.pool.acquire() as conn:
                    async for row in conn.cursor(sql, *params):
                        # Create entry
                        entry = MemoryEntry(
                            key=row["key"],
                            value=json.loads(row["content"]),
                            scope=MemoryScope(row["scope"]),
                            metadata=json.loads(row["metadata"]),
                        )

                        # Yield result
                        yield MemoryResult(
                            key=row["key"],
                            entry=entry.value,
                            similarity=1.0,
                        )

                _logger.debug(
                    "Retrieved memory entries",
                    extra={"store": "postgres", "query": query.dict()},
                )
            except Exception as e:
                _logger.error(
                    "Failed to retrieve from PostgreSQL",
                    extra={"error": str(e)},
                )
                raise RuntimeError(f"Failed to retrieve from PostgreSQL: {e}") from e

        return retrieve_generator()

    async def _delete_impl(self, key: str) -> bool:
        """Delete an entry from memory.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if not found

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    f"""
                    DELETE FROM {self.config.schema}.{self.config.table}
                    WHERE key = $1
                    """,
                    key,
                )
                # Parse the result string to get the number of rows deleted
                # Result format: "DELETE N" where N is the number of rows deleted
                rows_deleted = int(result.split()[-1])
                deleted = rows_deleted > 0

            _logger.debug(
                "Deleted memory entry",
                extra={"store": "postgres", "key": key, "deleted": deleted},
            )
            return deleted

        except Exception as e:
            _logger.error(
                "Failed to delete from PostgreSQL",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to delete from PostgreSQL: {e}") from e

    async def _exists_impl(self, key: str) -> bool:
        """Check if key exists in memory.

        Args:
            key: Key to check

        Returns:
            True if exists, False otherwise

        Raises:
            RuntimeError: If check fails
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(
                    f"""
                    SELECT EXISTS(
                        SELECT 1 FROM {self.config.schema}.{self.config.table}
                        WHERE key = $1
                    )
                    """,
                    key,
                )

            exists = bool(result) if result is not None else False
            _logger.debug(
                "Checked memory entry existence",
                extra={"store": "postgres", "key": key, "exists": exists},
            )
            return exists

        except Exception as e:
            _logger.error(
                "Failed to check existence in PostgreSQL",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to check existence in PostgreSQL: {e}") from e

    async def _clear_impl(self, scope: MemoryScope | None = None) -> int:
        """Clear entries from memory.

        Args:
            scope: Optional scope to clear

        Returns:
            Number of entries cleared

        Raises:
            RuntimeError: If clearing fails
        """
        try:
            async with self.pool.acquire() as conn:
                if scope is None:
                    result = await conn.execute(
                        f"""
                        DELETE FROM {self.config.schema}.{self.config.table}
                        """
                    )
                else:
                    result = await conn.execute(
                        f"""
                        DELETE FROM {self.config.schema}.{self.config.table}
                        WHERE scope = $1
                        """,
                        scope.value,
                    )

                cleared = int(result.split()[-1])

            _logger.debug(
                "Cleared memory entries",
                extra={"store": "postgres", "scope": scope, "cleared": cleared},
            )
            return cleared

        except Exception as e:
            _logger.error(
                "Failed to clear PostgreSQL store",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to clear PostgreSQL store: {e}") from e
