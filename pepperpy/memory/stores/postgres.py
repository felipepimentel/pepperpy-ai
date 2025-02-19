"""PostgreSQL memory store implementation."""

from collections.abc import AsyncIterator
from typing import Any, TypeVar

import asyncpg  # type: ignore
from asyncpg import Pool  # type: ignore

from pepperpy.core.errors import PepperpyError
from pepperpy.core.logging import get_logger
from pepperpy.memory.base import (
    BaseMemoryStore,
    MemoryEntry,
    MemoryQuery,
    MemorySearchResult,
)

# Configure logger
logger = get_logger(__name__)

T = TypeVar("T", bound=dict[str, Any])


class PostgresMemoryError(PepperpyError):
    """Error raised by PostgresMemoryStore."""

    def __init__(
        self,
        message: str,
        store_type: str = "postgres",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize error.

        Args:
            message: Error message
            store_type: Type of store that raised the error
            details: Additional error details
        """
        super().__init__(
            message=message,
            details={"store_type": store_type, **(details or {})},
        )


class PostgresMemoryStore(BaseMemoryStore[T]):
    """PostgreSQL-based memory store implementation."""

    pool: Pool | None = None

    def __init__(
        self,
        name: str,
        dsn: str,
        schema: str = "memory",
        table: str = "entries",
    ) -> None:
        """Initialize store.

        Args:
            name: Store name
            dsn: PostgreSQL connection string
            schema: Database schema name
            table: Table name
        """
        super().__init__(name)
        self.dsn = dsn
        self.schema = schema
        self.table = table

    async def _initialize(self) -> None:
        """Initialize database connection and schema."""
        try:
            self.pool = await asyncpg.create_pool(self.dsn)
            if not self.pool:
                raise PostgresMemoryError("Failed to create connection pool")

            async with self.pool.acquire() as conn:
                # Create schema if not exists
                await conn.execute("CREATE SCHEMA IF NOT EXISTS $1", self.schema)

                # Create table if not exists
                table_query = """
                CREATE TABLE IF NOT EXISTS $1.$2 (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    expires_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB
                )
                """
                await conn.execute(table_query, self.schema, self.table)

                # Create indices
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_type ON $1.$2 (type)",
                    self.schema,
                    self.table,
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_scope ON $1.$2 (scope)",
                    self.schema,
                    self.table,
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON $1.$2 (created_at)",
                    self.schema,
                    self.table,
                )
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_expires_at ON $1.$2 (expires_at)",
                    self.schema,
                    self.table,
                )

        except Exception as e:
            logger.error(
                "Failed to initialize PostgreSQL store",
                extra={
                    "store_type": self.__class__.__name__,
                    "error": str(e),
                },
            )
            raise PostgresMemoryError(
                "Failed to initialize PostgreSQL store",
                details={"error": str(e)},
            ) from e

    async def _cleanup(self) -> None:
        """Close database connection."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def _store(self, entry: MemoryEntry[T]) -> None:
        """Store a memory entry in the database.

        Args:
            entry: The memory entry to store.

        Raises:
            StorageError: If there is an error storing the entry.
        """
        entry_with_type = entry
        if not self.pool:
            raise PostgresMemoryError("Store not initialized")

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO $1.$2
                    (key, value, type, scope, created_at, expires_at, metadata)
                    VALUES ($3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        type = EXCLUDED.type,
                        scope = EXCLUDED.scope,
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at,
                        metadata = EXCLUDED.metadata
                    """,
                    self.schema,
                    self.table,
                    entry_with_type.key,
                    entry_with_type.value,
                    entry_with_type.type,
                    entry_with_type.scope,
                    entry_with_type.created_at,
                    entry_with_type.expires_at,
                    entry_with_type.metadata,
                )
        except Exception as e:
            logger.error(
                "Failed to store entry",
                extra={
                    "store_type": self.__class__.__name__,
                    "error": str(e),
                },
            )
            raise PostgresMemoryError(
                "Failed to store entry",
                details={"error": str(e), "key": entry.key},
            ) from e

    def _build_conditions(self, query: MemoryQuery) -> tuple[list[str], list[Any]]:
        """Build SQL conditions and parameters for the query.

        Args:
            query: The query parameters.

        Returns:
            A tuple of (conditions, parameters).
        """
        conditions = []
        params = []

        if query.key:
            conditions.append("key = $%d")
            params.append(query.key)

        if query.keys:
            placeholders = [f"${i + len(params) + 1}" for i in range(len(query.keys))]
            conditions.append(f"key = ANY(ARRAY[{','.join(placeholders)}])")
            params.extend(query.keys)

        if query.metadata:
            for key, value in query.metadata.items():
                conditions.append(f"metadata->>{len(params) + 1} = ${len(params) + 2}")
                params.extend([key, str(value)])

        if query.filters:
            for key, value in query.filters.items():
                conditions.append(f"metadata->>{len(params) + 1} = ${len(params) + 2}")
                params.extend([key, str(value)])

        return conditions, params

    def _build_order_clause(self, query: MemoryQuery) -> tuple[str, str]:
        """Build the ORDER BY clause for the query.

        Args:
            query: The query parameters.

        Returns:
            A tuple of (order_field, order_direction).
        """
        order_field = query.order_by if query.order_by else "created_at"
        order_direction = query.order if query.order else "ASC"
        return order_field, order_direction

    def _build_sql_query(
        self, conditions: list[str], params: list[Any], query: MemoryQuery
    ) -> tuple[str, list[Any]]:
        """Build the SQL query and parameters.

        Args:
            conditions: The WHERE conditions.
            params: The query parameters.
            query: The original query object.

        Returns:
            A tuple of (sql_query, parameters).
        """
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        order_field, order_direction = self._build_order_clause(query)

        sql = """
            SELECT * FROM $1.$2
            WHERE $3
            ORDER BY $4 $5
        """

        if query.limit:
            sql += " LIMIT $" + str(len(params) + 1)
            params.append(query.limit)

        if query.offset:
            sql += " OFFSET $" + str(len(params) + 1)
            params.append(query.offset)

        return sql, [
            *[self.schema, self.table, where_clause, order_field, order_direction],
            *params,
        ]

    async def _retrieve(
        self,
        query: MemoryQuery,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Retrieve entries from memory.

        Args:
            query: Query parameters.

        Yields:
            Memory search results.

        Raises:
            PostgresMemoryError: If retrieval fails.
        """
        if not self.pool:
            raise PostgresMemoryError("Store not initialized")

        try:
            conditions, params = self._build_conditions(query)
            sql_query, final_params = self._build_sql_query(conditions, params, query)

            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    async for row in conn.cursor(sql_query, *final_params):
                        entry = MemoryEntry[T](
                            key=row["key"],
                            value=row["value"],
                            type=row["type"],
                            scope=row["scope"],
                            created_at=row["created_at"],
                            expires_at=row["expires_at"],
                            metadata=row["metadata"],
                        )
                        # Default score since we don't do semantic search here
                        # No highlights for basic retrieval
                        yield MemorySearchResult[T](
                            entry=entry,
                            score=1.0,
                            highlights=[],
                            metadata={},
                        )

        except Exception as e:
            logger.error(
                "Failed to retrieve entries",
                extra={
                    "store_type": self.__class__.__name__,
                    "error": str(e),
                },
            )
            raise PostgresMemoryError(
                "Failed to retrieve entries",
                details={"error": str(e)},
            ) from e

    async def search(self, query: MemoryQuery) -> AsyncIterator[MemorySearchResult[T]]:
        """Search memory entries.

        Args:
            query: Search parameters

        Yields:
            Search results ordered by relevance

        Raises:
            ValueError: If query is invalid
            MemoryError: If search fails
        """
        async for result in self._retrieve(query):
            yield result

    async def _delete(self, key: str) -> None:
        """Delete entry from database.

        Args:
            key: Key of entry to delete
        """
        if not self.pool:
            raise PostgresMemoryError("Store not initialized")

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM $1.$2 WHERE key = $3",
                    self.schema,
                    self.table,
                    key,
                )
        except Exception as e:
            logger.error(
                "Failed to delete entry",
                extra={
                    "store_type": self.__class__.__name__,
                    "error": str(e),
                },
            )
            raise PostgresMemoryError(
                "Failed to delete entry",
                details={"error": str(e), "key": key},
            ) from e

    async def similar(
        self,
        key: str,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> AsyncIterator[MemorySearchResult[T]]:
        """Find similar entries.

        Args:
            key: Memory key to find similar entries for
            limit: Maximum number of results
            min_score: Minimum similarity score

        Yields:
            Similar entries ordered by similarity

        Raises:
            KeyError: If key not found
            ValueError: If parameters are invalid
            MemoryError: If similarity search fails
        """
        # For now, just return entries with the same key
        query = MemoryQuery(
            query="",
            key=key,
            limit=limit,
            min_score=min_score,
        )
        async for result in self._retrieve(query):
            yield result
