"""SQLite document store implementation for Pepperpy."""

import asyncio
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar

from ...common.errors import StorageError
from .base import Document, DocumentStore

logger = logging.getLogger(__name__)

class SQLiteDocumentStore(DocumentStore):
    """SQLite document store implementation."""
    
    def __init__(
        self,
        name: str,
        store_path: str,
    ) -> None:
        """Initialize SQLite document store.
        
        Args:
            name: Store name
            store_path: Path to SQLite database file
        """
        super().__init__(name, store_path)
        self._conn: Optional[sqlite3.Connection] = None
        
    async def _initialize(self) -> None:
        """Initialize SQLite database."""
        # Create parent directory if needed
        path = Path(self._store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database
        self._conn = sqlite3.connect(str(path))
        
        # Create tables
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT
            )
        """)
        self._conn.commit()
        
        logger.debug(f"Initialized SQLite database at {path}")
        
    async def _cleanup(self) -> None:
        """Cleanup SQLite database."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            
    async def _add(self, documents: List[Document]) -> None:
        """Add documents to SQLite database."""
        cursor = self._conn.cursor()
        
        # Insert documents
        for doc in documents:
            cursor.execute(
                "INSERT OR REPLACE INTO documents (id, content, metadata) VALUES (?, ?, ?)",
                (doc.id, doc.content, json.dumps(doc.metadata)),
            )
            
        self._conn.commit()
        logger.debug(f"Added {len(documents)} documents to SQLite database")
        
    async def _get(self, id: str) -> Optional[Document]:
        """Get document from SQLite database."""
        cursor = self._conn.cursor()
        
        # Query document
        cursor.execute(
            "SELECT content, metadata FROM documents WHERE id = ?",
            (id,),
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
            
        # Create document
        content, metadata_json = row
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        return Document(id=id, content=content, metadata=metadata)
        
    async def _search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search SQLite database."""
        cursor = self._conn.cursor()
        
        # Build query
        sql = "SELECT id, content, metadata FROM documents WHERE content LIKE ?"
        params = [f"%{query}%"]
        
        if filters:
            # Add metadata filters
            for key, value in filters.items():
                sql += f" AND json_extract(metadata, '$.{key}') = ?"
                params.append(value)
                
        sql += f" LIMIT {limit}"
        
        # Execute query
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Create documents
        documents = []
        for id_, content, metadata_json in rows:
            metadata = json.loads(metadata_json) if metadata_json else {}
            documents.append(Document(id=id_, content=content, metadata=metadata))
            
        return documents
        
    async def _delete(self, ids: List[str]) -> None:
        """Delete documents from SQLite database."""
        cursor = self._conn.cursor()
        
        # Delete documents
        placeholders = ",".join("?" * len(ids))
        cursor.execute(f"DELETE FROM documents WHERE id IN ({placeholders})", ids)
        
        self._conn.commit()
        logger.debug(f"Deleted {len(ids)} documents from SQLite database")
        
    async def _clear(self) -> None:
        """Clear SQLite database."""
        cursor = self._conn.cursor()
        
        # Delete all documents
        cursor.execute("DELETE FROM documents")
        
        self._conn.commit()
        logger.debug("Cleared SQLite database")
        
    def __repr__(self) -> str:
        """Return string representation."""
        cursor = self._conn.cursor() if self._conn else None
        count = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0] if cursor else 0
        
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"store_path={self.store_path}, "
            f"documents={count}"
            f")"
        ) 