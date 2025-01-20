"""SQLite store implementation."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from .base import DataStore, DataStoreError


logger = logging.getLogger(__name__)


class SQLiteStore(DataStore):
    """SQLite store implementation."""
    
    def __init__(
        self,
        name: str,
        path: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize SQLite store.
        
        Args:
            name: Store name
            path: Database file path
            config: Optional store configuration
        """
        super().__init__(name, config)
        self._path = path
        self._conn: Optional[sqlite3.Connection] = None
        
    async def _initialize(self) -> None:
        """Initialize SQLite store."""
        await super()._initialize()
        try:
            # Create parent directories if needed
            db_path = Path(self._path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self._conn = sqlite3.connect(self._path)
            
            # Create table if not exists
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            self._conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to initialize store: {e}") from e
            
    async def _cleanup(self) -> None:
        """Clean up SQLite store."""
        await super()._cleanup()
        try:
            if self._conn:
                self._conn.close()
                self._conn = None
                
        except Exception as e:
            raise DataStoreError(f"Failed to clean up store: {e}") from e
            
    async def get(
        self,
        key: str,
        default: Optional[Any] = None,
    ) -> Optional[Any]:
        """Get value by key.
        
        Args:
            key: Key to get
            default: Optional default value
            
        Returns:
            Value if found, default otherwise
            
        Raises:
            DataStoreError: If retrieval fails
        """
        try:
            if not self._conn:
                raise DataStoreError("Store not initialized")
                
            cursor = self._conn.cursor()
            cursor.execute("SELECT value FROM store WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row is None:
                return default
                
            return json.loads(row[0])
            
        except Exception as e:
            raise DataStoreError(f"Failed to get value for key {key}: {e}") from e
            
    async def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set value by key.
        
        Args:
            key: Key to set
            value: Value to set
            
        Raises:
            DataStoreError: If setting fails
        """
        try:
            if not self._conn:
                raise DataStoreError("Store not initialized")
                
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO store (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
            self._conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to set value for key {key}: {e}") from e
            
    async def delete(
        self,
        key: str,
    ) -> None:
        """Delete value by key.
        
        Args:
            key: Key to delete
            
        Raises:
            DataStoreError: If deletion fails
        """
        try:
            if not self._conn:
                raise DataStoreError("Store not initialized")
                
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM store WHERE key = ?", (key,))
            self._conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to delete key {key}: {e}") from e
            
    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if key exists.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, False otherwise
            
        Raises:
            DataStoreError: If check fails
        """
        try:
            if not self._conn:
                raise DataStoreError("Store not initialized")
                
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1 FROM store WHERE key = ?", (key,))
            return cursor.fetchone() is not None
            
        except Exception as e:
            raise DataStoreError(f"Failed to check key {key}: {e}") from e
            
    async def clear(self) -> None:
        """Clear all values.
        
        Raises:
            DataStoreError: If clearing fails
        """
        try:
            if not self._conn:
                raise DataStoreError("Store not initialized")
                
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM store")
            self._conn.commit()
            
        except Exception as e:
            raise DataStoreError(f"Failed to clear store: {e}") from e
            
    def validate(self) -> None:
        """Validate SQLite store state."""
        super().validate()
        
        if not self._path:
            raise ValueError("Database path cannot be empty") 