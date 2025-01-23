"""SQLite store implementation."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .base import DataStore, DataStoreError


logger = logging.getLogger(__name__)


class SQLiteStore(DataStore):
    """SQLite store implementation."""
    
    def __init__(
        self,
        name: str,
        path: Union[str, Path],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize SQLite store.
        
        Args:
            name: Store name
            path: Path to SQLite database file
            config: Optional store configuration
        """
        super().__init__(name, config)
        self.path = Path(path)
        self._conn: Optional[sqlite3.Connection] = None
        
    async def _initialize(self) -> None:
        """Initialize store.
        
        Creates database file and tables if they don't exist.
        
        Raises:
            DataStoreError: If initialization fails
        """
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(self.path))
            
            if self._conn is None:
                raise DataStoreError("Failed to create SQLite connection")
                
            cursor = self._conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self._conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to initialize store: {e}")
            
    async def _cleanup(self) -> None:
        """Clean up store.
        
        Closes database connection.
        
        Raises:
            DataStoreError: If cleanup fails
        """
        try:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
        except Exception as e:
            raise DataStoreError(f"Failed to clean up store: {e}")
            
    def _validate_connection(self) -> sqlite3.Connection:
        """Validate database connection.
        
        Returns:
            Active SQLite connection
            
        Raises:
            DataStoreError: If connection is not initialized
        """
        if self._conn is None:
            raise DataStoreError("Store not initialized")
        return self._conn
            
    async def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Optional[Any]:
        """Get value by key.
        
        Args:
            key: Storage key
            default: Default value if key not found
            
        Returns:
            Retrieved value or default if not found
            
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            conn = self._validate_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM store WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row is None:
                return default
                
            return json.loads(row[0])
            
        except Exception as e:
            raise DataStoreError(f"Failed to get value: {e}")
            
    async def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set value for key.
        
        Args:
            key: Storage key
            value: Value to store
            
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            conn = self._validate_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO store (key, value)
                VALUES (?, ?)
                """,
                (key, json.dumps(value)),
            )
            conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to set value: {e}")
            
    async def delete(
        self,
        key: str,
    ) -> None:
        """Delete value by key.
        
        Args:
            key: Storage key
            
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            conn = self._validate_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM store WHERE key = ?", (key,))
            conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to delete value: {e}")
            
    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if key exists.
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists, False otherwise
            
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            conn = self._validate_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM store WHERE key = ?", (key,))
            return cursor.fetchone() is not None
            
        except Exception as e:
            raise DataStoreError(f"Failed to check key existence: {e}")
            
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            DataStoreError: If storage operation fails
        """
        try:
            conn = self._validate_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM store")
            conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to clear store: {e}") 