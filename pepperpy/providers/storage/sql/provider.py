"""SQL storage provider implementation.

This module provides functionality for interacting with SQL databases,
including connection management, query execution, and result processing.
"""

from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

from pepperpy.providers.storage.base import StorageError, StorageProvider


class SQLStorageProvider(StorageProvider):
    """SQL storage provider for database operations."""

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        table_name: str = "storage",
    ):
        """Initialize SQL storage provider.

        Args:
            connection_string: Database connection string
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to overflow
            pool_timeout: Pool timeout in seconds
            pool_recycle: Connection recycle time in seconds
            table_name: Table name for storing data

        Raises:
            ImportError: If SQLAlchemy is not installed
            StorageError: If initialization fails
        """
        super().__init__()
        try:
            import sqlalchemy
            from sqlalchemy import create_engine
        except ImportError:
            raise ImportError(
                "SQLAlchemy is required for SQLStorageProvider. "
                "Install it with: pip install sqlalchemy"
            )

        self.connection_string = connection_string
        self.table_name = table_name
        self.db_type = self._get_db_type(connection_string)

        try:
            self.engine = create_engine(
                connection_string,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
            )
            self.metadata = sqlalchemy.MetaData()
            self.connection = None
        except Exception as e:
            raise StorageError(f"Failed to initialize SQL storage: {e}")

    async def initialize(self) -> None:
        """Initialize the database connection and create tables if needed.

        Raises:
            StorageError: If initialization fails
        """
        try:
            import sqlalchemy

            self.connection = self.engine.connect()

            # Create storage table if it doesn't exist
            if not self.engine.dialect.has_table(self.connection, self.table_name):
                table = sqlalchemy.Table(
                    self.table_name,
                    self.metadata,
                    sqlalchemy.Column("key", sqlalchemy.String, primary_key=True),
                    sqlalchemy.Column("data", sqlalchemy.LargeBinary, nullable=False),
                    sqlalchemy.Column(
                        "created_at", sqlalchemy.DateTime, default=sqlalchemy.func.now()
                    ),
                    sqlalchemy.Column(
                        "updated_at",
                        sqlalchemy.DateTime,
                        default=sqlalchemy.func.now(),
                        onupdate=sqlalchemy.func.now(),
                    ),
                )
                table.create(self.engine)
        except Exception as e:
            raise StorageError(f"Failed to initialize database: {e}")

    async def cleanup(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def _get_db_type(self, connection_string: str) -> str:
        """Get the database type from the connection string.

        Args:
            connection_string: Database connection string

        Returns:
            Database type (e.g., 'sqlite', 'postgresql', 'mysql')
        """
        parsed = urlparse(connection_string)
        return parsed.scheme.split("+")[0]

    def store(self, path: Union[str, Path], data: Union[str, bytes]) -> None:
        """Store data in the database.

        Args:
            path: Key to store data under
            data: Data to store

        Raises:
            StorageError: If storage operation fails
        """
        try:
            from sqlalchemy import text

            if not self.connection:
                self.initialize()

            # Convert string to bytes if needed
            if isinstance(data, str):
                data = data.encode("utf-8")

            # Check if key exists
            query = text(f"SELECT 1 FROM {self.table_name} WHERE key = :key")
            result = self.connection.execute(query, {"key": str(path)})
            exists = result.fetchone() is not None

            if exists:
                # Update existing record
                query = text(
                    f"UPDATE {self.table_name} SET data = :data, updated_at = CURRENT_TIMESTAMP WHERE key = :key"
                )
                self.connection.execute(query, {"key": str(path), "data": data})
            else:
                # Insert new record
                query = text(
                    f"INSERT INTO {self.table_name} (key, data) VALUES (:key, :data)"
                )
                self.connection.execute(query, {"key": str(path), "data": data})

            self.connection.commit()
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            raise StorageError(f"Failed to store data in database: {e}")

    def retrieve(self, path: Union[str, Path]) -> bytes:
        """Retrieve data from the database.

        Args:
            path: Key to retrieve data for

        Returns:
            Retrieved data

        Raises:
            StorageError: If retrieval operation fails
        """
        try:
            from sqlalchemy import text

            if not self.connection:
                self.initialize()

            query = text(f"SELECT data FROM {self.table_name} WHERE key = :key")
            result = self.connection.execute(query, {"key": str(path)})
            row = result.fetchone()

            if not row:
                raise StorageError(f"Key not found: {path}")

            return row[0]
        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Failed to retrieve data from database: {e}")
            raise

    def delete(self, path: Union[str, Path]) -> bool:
        """Delete data from the database.

        Args:
            path: Key to delete data for

        Returns:
            True if deleted, False if not found

        Raises:
            StorageError: If deletion operation fails
        """
        try:
            from sqlalchemy import text

            if not self.connection:
                self.initialize()

            query = text(f"DELETE FROM {self.table_name} WHERE key = :key")
            result = self.connection.execute(query, {"key": str(path)})
            self.connection.commit()

            return result.rowcount > 0
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            raise StorageError(f"Failed to delete data from database: {e}")

    def exists(self, path: Union[str, Path]) -> bool:
        """Check if data exists in the database.

        Args:
            path: Key to check

        Returns:
            True if exists, False otherwise

        Raises:
            StorageError: If check operation fails
        """
        try:
            from sqlalchemy import text

            if not self.connection:
                self.initialize()

            query = text(f"SELECT 1 FROM {self.table_name} WHERE key = :key")
            result = self.connection.execute(query, {"key": str(path)})

            return result.fetchone() is not None
        except Exception as e:
            raise StorageError(f"Failed to check existence in database: {e}")

    def list_files(self, path: Optional[Union[str, Path]] = None) -> List[str]:
        """List keys in the database.

        Args:
            path: Optional prefix to filter keys by

        Returns:
            List of keys

        Raises:
            StorageError: If list operation fails
        """
        try:
            from sqlalchemy import text

            if not self.connection:
                self.initialize()

            if path:
                # Filter by prefix
                prefix = str(path)
                query = text(
                    f"SELECT key FROM {self.table_name} WHERE key LIKE :prefix"
                )
                result = self.connection.execute(query, {"prefix": f"{prefix}%"})
            else:
                # Get all keys
                query = text(f"SELECT key FROM {self.table_name}")
                result = self.connection.execute(query)

            return [row[0] for row in result]
        except Exception as e:
            raise StorageError(f"Failed to list keys from database: {e}")

    def get_url(self, path: Union[str, Path], expires_in: Optional[int] = None) -> str:
        """Get a URL for accessing the data.

        Note: SQL storage doesn't support direct URLs, so this returns a pseudo-URL.

        Args:
            path: Key to get URL for
            expires_in: Optional expiration time in seconds (ignored)

        Returns:
            Pseudo-URL for the data

        Raises:
            StorageError: If URL generation fails
        """
        try:
            if not self.exists(path):
                raise StorageError(f"Key not found: {path}")

            # Return a pseudo-URL since SQL storage doesn't have direct URLs
            return f"sql://{self.db_type}/{self.table_name}/{path}"
        except Exception as e:
            if not isinstance(e, StorageError):
                raise StorageError(f"Failed to generate URL: {e}")
            raise
