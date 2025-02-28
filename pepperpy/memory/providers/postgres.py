"""PostgreSQL-based memory provider implementation."""

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from pepperpy.memory.errors import MemoryError
from pepperpy.memory.providers.base import MemoryProvider


class PostgresMemoryProvider(MemoryProvider):
    """PostgreSQL-based memory provider implementation."""

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
            MemoryError: If connection fails
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

        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                **kwargs,
            )
            self._ensure_table_exists()
        except Exception as e:
            raise MemoryError(f"Failed to connect to PostgreSQL: {e}")

    def _ensure_table_exists(self) -> None:
        """Ensure the memory store table exists."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        key TEXT PRIMARY KEY,
                        value JSONB NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.conn.commit()
        except Exception as e:
            raise MemoryError(f"Failed to create table: {e}")

    def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a value in PostgreSQL.

        Args:
            key: Key to store value under
            value: Value to store
            metadata: Optional metadata to store

        Raises:
            MemoryError: If storage operation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} (key, value, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET value = EXCLUDED.value,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    (
                        key,
                        json.dumps(value),
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                self.conn.commit()
        except Exception as e:
            raise MemoryError(f"Failed to store value: {e}")

    def retrieve(
        self,
        key: str,
        include_metadata: bool = False,
    ) -> Union[Any, Tuple[Any, Dict[str, Any]]]:
        """Retrieve a value from PostgreSQL.

        Args:
            key: Key to retrieve value for
            include_metadata: Whether to include metadata

        Returns:
            Union[Any, Tuple[Any, Dict[str, Any]]]: Value or (value, metadata) tuple

        Raises:
            MemoryError: If retrieval operation fails
            KeyError: If key not found
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT value, metadata
                    FROM {self.table_name}
                    WHERE key = %s
                """,
                    (key,),
                )
                result = cur.fetchone()

                if not result:
                    raise KeyError(f"Key not found: {key}")

                value = json.loads(result[0])
                metadata = json.loads(result[1]) if result[1] else {}

                return (value, metadata) if include_metadata else value

        except KeyError:
            raise
        except Exception as e:
            raise MemoryError(f"Failed to retrieve value: {e}")

    def delete(self, key: str) -> bool:
        """Delete a value from PostgreSQL.

        Args:
            key: Key to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            MemoryError: If deletion operation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    DELETE FROM {self.table_name}
                    WHERE key = %s
                    RETURNING key
                """,
                    (key,),
                )
                self.conn.commit()
                return bool(cur.fetchone())
        except Exception as e:
            raise MemoryError(f"Failed to delete value: {e}")

    def clear(self) -> None:
        """Clear all values from PostgreSQL.

        Raises:
            MemoryError: If clear operation fails
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {self.table_name}")
                self.conn.commit()
        except Exception as e:
            raise MemoryError(f"Failed to clear values: {e}")

    def list_keys(
        self,
        pattern: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[str]:
        """List keys in PostgreSQL.

        Args:
            pattern: Optional pattern to filter keys (SQL LIKE pattern)
            limit: Optional maximum number of keys to return

        Returns:
            List[str]: List of keys

        Raises:
            MemoryError: If list operation fails
        """
        try:
            with self.conn.cursor() as cur:
                query = f"SELECT key FROM {self.table_name}"
                params = []

                if pattern:
                    query += " WHERE key LIKE %s"
                    params.append(pattern)

                if limit:
                    query += " LIMIT %s"
                    params.append(limit)

                cur.execute(query, params)
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            raise MemoryError(f"Failed to list keys: {e}")

    def close(self) -> None:
        """Close the PostgreSQL connection.

        Raises:
            MemoryError: If close operation fails
        """
        try:
            self.conn.close()
        except Exception as e:
            raise MemoryError(f"Failed to close connection: {e}")

    def __del__(self) -> None:
        """Ensure connection is closed on deletion."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup
