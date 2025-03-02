"""PostgreSQL-based memory provider implementation."""

import json
import time
from typing import Any, Dict, List, Optional, TypeVar, cast

from pepperpy.core.errors import ProviderError
from pepperpy.providers.memory.base import MemoryItem, MemoryProvider

T = TypeVar("T")


class PostgresMemoryProvider(MemoryProvider[T]):
    """Provider implementation for PostgreSQL-based memory storage."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "pepperpy",
        user: str = "postgres",
        password: Optional[str] = None,
        table_name: str = "memory_store",
        **kwargs,
    ):
        """Initialize PostgreSQL memory provider.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            table_name: Table name for storing data
            **kwargs: Additional connection parameters

        Raises:
            ImportError: If psycopg2 package is not installed
            ProviderError: If connection fails
        """
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise ImportError(
                "psycopg2 package is required for PostgresMemoryProvider. "
                "Install it with: pip install psycopg2-binary"
            )

        self.table_name = table_name
        self.conn = None
        self.conn_params = {
            "host": host,
            "port": port,
            "database": database,
            "user": user,
            "password": password,
            **kwargs,
        }

    async def initialize(self) -> None:
        """Initialize the provider.

        Raises:
            ProviderError: If initialization fails
        """
        try:
            import psycopg2

            self.conn = psycopg2.connect(**self.conn_params)
            await self._ensure_table_exists()
        except Exception as e:
            raise ProviderError(f"Failed to initialize PostgreSQL provider: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.conn:
            self.conn.close()
            self.conn = None

    async def _ensure_table_exists(self) -> None:
        """Ensure the memory table exists.

        Raises:
            ProviderError: If table creation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        key TEXT PRIMARY KEY,
                        value JSONB NOT NULL,
                        created_at DOUBLE PRECISION NOT NULL,
                        expires_at DOUBLE PRECISION,
                        metadata JSONB
                    )
                    """
                )
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to create table: {e}")

    async def get(self, key: str) -> Optional[T]:
        """Get value by key.

        Args:
            key: Key to get

        Returns:
            Value associated with key or None if not found

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT value, expires_at FROM {self.table_name} WHERE key = %s",
                    (key,),
                )
                result = cursor.fetchone()
                if not result:
                    return None

                value_json, expires_at = result

                # Check if expired
                if expires_at and expires_at < time.time():
                    await self.delete(key)
                    return None

                return cast(T, json.loads(value_json))
        except Exception as e:
            raise ProviderError(f"Failed to get value: {e}")

    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple values by keys.

        Args:
            keys: Keys to get

        Returns:
            Dictionary mapping keys to values

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        result: Dict[str, T] = {}
        if not keys:
            return result

        try:
            placeholders = ", ".join(["%s"] * len(keys))
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT key, value, expires_at FROM {self.table_name} "
                    f"WHERE key IN ({placeholders})",
                    tuple(keys),
                )
                rows = cursor.fetchall()

                now = time.time()
                expired_keys = []

                for key, value_json, expires_at in rows:
                    # Check if expired
                    if expires_at and expires_at < now:
                        expired_keys.append(key)
                        continue

                    result[key] = cast(T, json.loads(value_json))

                # Delete expired keys
                if expired_keys:
                    await self.delete_many(expired_keys)

            return result
        except Exception as e:
            raise ProviderError(f"Failed to get multiple values: {e}")

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem[T]:
        """Set value by key.

        Args:
            key: Key to set
            value: Value to set
            ttl: Time to live in seconds
            metadata: Optional metadata

        Returns:
            Memory item

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            # Create memory item
            now = time.time()
            expires_at = now + ttl if ttl is not None else None
            item = MemoryItem[T](
                value=value,
                created_at=now,
                expires_at=expires_at,
                metadata=metadata or {},
            )

            # Store in PostgreSQL
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {self.table_name} (key, value, created_at, expires_at, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at,
                        metadata = EXCLUDED.metadata
                    """,
                    (
                        key,
                        json.dumps(value),
                        item.created_at,
                        item.expires_at,
                        json.dumps(item.metadata),
                    ),
                )
                self.conn.commit()

            return item
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to set value: {e}")

    async def set_many(
        self,
        items: Dict[str, T],
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem[T]]:
        """Set multiple values.

        Args:
            items: Dictionary mapping keys to values
            ttl: Time to live in seconds
            metadata: Optional metadata

        Returns:
            List of memory items

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        result: List[MemoryItem[T]] = []
        if not items:
            return result

        try:
            # Create memory items
            now = time.time()
            expires_at = now + ttl if ttl is not None else None
            memory_items = {}

            for key, value in items.items():
                item = MemoryItem[T](
                    value=value,
                    created_at=now,
                    expires_at=expires_at,
                    metadata=metadata or {},
                )
                memory_items[key] = item
                result.append(item)

            # Store in PostgreSQL
            with self.conn.cursor() as cursor:
                values = []
                for key, item in memory_items.items():
                    values.append((
                        key,
                        json.dumps(item.value),
                        item.created_at,
                        item.expires_at,
                        json.dumps(item.metadata),
                    ))

                # Use executemany for better performance
                cursor.executemany(
                    f"""
                    INSERT INTO {self.table_name} (key, value, created_at, expires_at, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        value = EXCLUDED.value,
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at,
                        metadata = EXCLUDED.metadata
                    """,
                    values,
                )
                self.conn.commit()

            return result
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to set multiple values: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value by key.

        Args:
            key: Key to delete

        Returns:
            True if key was deleted, False otherwise

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {self.table_name} WHERE key = %s RETURNING key",
                    (key,),
                )
                result = cursor.fetchone()
                self.conn.commit()
                return result is not None
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to delete value: {e}")

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        if not keys:
            return 0

        try:
            placeholders = ", ".join(["%s"] * len(keys))
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {self.table_name} WHERE key IN ({placeholders}) RETURNING key",
                    tuple(keys),
                )
                result = cursor.fetchall()
                self.conn.commit()
                return len(result)
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to delete multiple values: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT 1 FROM {self.table_name} WHERE key = %s AND "
                    f"(expires_at IS NULL OR expires_at > %s)",
                    (key, time.time()),
                )
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            raise ProviderError(f"Failed to check key existence: {e}")

    async def clear(self) -> None:
        """Clear all values.

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"DELETE FROM {self.table_name}")
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to clear values: {e}")

    async def get_metadata(self, key: str) -> Optional[MemoryItem[T]]:
        """Get item metadata.

        Args:
            key: Key to get metadata for

        Returns:
            Memory item or None if key does not exist

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT value, created_at, expires_at, metadata FROM {self.table_name} "
                    f"WHERE key = %s",
                    (key,),
                )
                result = cursor.fetchone()
                if not result:
                    return None

                value_json, created_at, expires_at, metadata_json = result

                # Check if expired
                if expires_at and expires_at < time.time():
                    await self.delete(key)
                    return None

                return MemoryItem[T](
                    value=cast(T, json.loads(value_json)),
                    created_at=created_at,
                    expires_at=expires_at,
                    metadata=json.loads(metadata_json) if metadata_json else {},
                )
        except Exception as e:
            raise ProviderError(f"Failed to get metadata: {e}")

    async def update_metadata(
        self, key: str, metadata: Dict[str, Any]
    ) -> Optional[MemoryItem[T]]:
        """Update item metadata.

        Args:
            key: Key to update metadata for
            metadata: New metadata

        Returns:
            Updated memory item or None if key does not exist

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            # Get current item
            item = await self.get_metadata(key)
            if not item:
                return None

            # Update metadata
            item.metadata.update(metadata)

            # Store updated item
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {self.table_name} SET metadata = %s WHERE key = %s RETURNING 1",
                    (json.dumps(item.metadata), key),
                )
                result = cursor.fetchone()
                self.conn.commit()

                if not result:
                    return None

            return item
        except Exception as e:
            self.conn.rollback()
            raise ProviderError(f"Failed to update metadata: {e}")

    async def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern.

        Args:
            pattern: Pattern to match keys against

        Returns:
            List of matching keys

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                if pattern:
                    cursor.execute(
                        f"SELECT key FROM {self.table_name} WHERE key LIKE %s AND "
                        f"(expires_at IS NULL OR expires_at > %s)",
                        (f"%{pattern}%", time.time()),
                    )
                else:
                    cursor.execute(
                        f"SELECT key FROM {self.table_name} WHERE "
                        f"expires_at IS NULL OR expires_at > %s",
                        (time.time(),),
                    )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            raise ProviderError(f"Failed to get keys: {e}")

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for key.

        Args:
            key: Key to get TTL for

        Returns:
            Remaining TTL in seconds or None if key does not exist or has no TTL

        Raises:
            ProviderError: If operation fails
        """
        if not self.conn:
            raise ProviderError("PostgreSQL connection not initialized")

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT expires_at FROM {self.table_name} WHERE key = %s",
                    (key,),
                )
                result = cursor.fetchone()
                if not result or result[0] is None:
                    return None

                expires_at = result[0]
                ttl = int(expires_at - time.time())
                return ttl if ttl > 0 else None
        except Exception as e:
            raise ProviderError(f"Failed to get TTL: {e}")
