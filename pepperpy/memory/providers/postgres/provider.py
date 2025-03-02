"""PostgreSQL memory provider implementation."""

from typing import Any, Dict, List, Optional, Union

from pepperpy.memory.providers.base import BaseMemoryProvider


class PostgresMemoryProvider(BaseMemoryProvider):
    """Provider implementation for PostgreSQL memory storage."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "pepperpy_memory",
        **kwargs: Any,
    ):
        """Initialize PostgreSQL memory provider.

        Args:
            connection_string: PostgreSQL connection string
            table_name: Table name for memory storage
            **kwargs: Additional provider options
        """
        super().__init__(**kwargs)
        self.connection_string = connection_string
        self.table_name = table_name
        self._connection = None
        self._cursor = None
        self._ensure_table_exists()

    def _get_connection(self):
        """Get or create PostgreSQL connection.

        Returns:
            PostgreSQL connection
        """
        if self._connection is None:
            try:
                import psycopg2
                import psycopg2.extras
                self._connection = psycopg2.connect(self.connection_string)
            except ImportError:
                raise ImportError(
                    "psycopg2 package is required to use PostgresMemoryProvider. "
                    "Install it with `pip install psycopg2-binary`."
                )
        return self._connection

    def _get_cursor(self):
        """Get or create PostgreSQL cursor.

        Returns:
            PostgreSQL cursor
        """
        if self._cursor is None or self._cursor.closed:
            conn = self._get_connection()
            import psycopg2.extras
            self._cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return self._cursor

    def _ensure_table_exists(self):
        """Ensure the memory table exists.

        Raises:
            ValueError: If table creation fails
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    key TEXT PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
            )
            self._connection.commit()
        except Exception as e:
            raise ValueError(f"Failed to create memory table: {e}")

    def store(self, key: str, data: Any) -> None:
        """Store data in PostgreSQL.

        Args:
            key: The key to store the data under
            data: The data to store

        Raises:
            ValueError: If storage operation fails
        """
        try:
            import json
            cursor = self._get_cursor()
            serialized = json.dumps(data)
            cursor.execute(
                f"""
                INSERT INTO {self.table_name} (key, data, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (key) 
                DO UPDATE SET data = %s, updated_at = NOW()
                """,
                (key, serialized, serialized),
            )
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise ValueError(f"Failed to store data in PostgreSQL: {e}")

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from PostgreSQL.

        Args:
            key: The key to retrieve the data from

        Returns:
            The retrieved data, or None if the key does not exist

        Raises:
            ValueError: If retrieval operation fails
        """
        try:
            import json
            cursor = self._get_cursor()
            cursor.execute(
                f"SELECT data FROM {self.table_name} WHERE key = %s",
                (key,),
            )
            result = cursor.fetchone()
            if result is None:
                return None
            return json.loads(result[0])
        except Exception as e:
            raise ValueError(f"Failed to retrieve data from PostgreSQL: {e}")

    def delete(self, key: str) -> bool:
        """Delete data from PostgreSQL.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False otherwise

        Raises:
            ValueError: If deletion operation fails
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(
                f"DELETE FROM {self.table_name} WHERE key = %s",
                (key,),
            )
            self._connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._connection.rollback()
            raise ValueError(f"Failed to delete data from PostgreSQL: {e}")

    def list_keys(self, pattern: str = "%") -> List[str]:
        """List keys in PostgreSQL.

        Args:
            pattern: The pattern to filter keys by (SQL LIKE pattern)

        Returns:
            A list of keys

        Raises:
            ValueError: If list operation fails
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(
                f"SELECT key FROM {self.table_name} WHERE key LIKE %s",
                (pattern,),
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            raise ValueError(f"Failed to list keys in PostgreSQL: {e}")

    def exists(self, key: str) -> bool:
        """Check if a key exists in PostgreSQL.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise

        Raises:
            ValueError: If check operation fails
        """
        try:
            cursor = self._get_cursor()
            cursor.execute(
                f"SELECT 1 FROM {self.table_name} WHERE key = %s",
                (key,),
            )
            return cursor.fetchone() is not None
        except Exception as e:
            raise ValueError(f"Failed to check key existence in PostgreSQL: {e}")

    def close(self):
        """Close the PostgreSQL connection.

        Raises:
            ValueError: If connection close fails
        """
        try:
            if self._cursor is not None and not self._cursor.closed:
                self._cursor.close()
                self._cursor = None
            if self._connection is not None:
                self._connection.close()
                self._connection = None
        except Exception as e:
            raise ValueError(f"Failed to close PostgreSQL connection: {e}")
