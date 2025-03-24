"""SQLite RAG provider implementation."""

import sqlite3
from typing import Any, Dict, List, Optional

import numpy as np

from ..base import RAGProvider
from ..errors import RAGError
from ..models import Document, SearchResult


class SQLiteRAGProvider(RAGProvider):
    """SQLite-based RAG provider."""

    def __init__(
        self,
        database_path: str,
        table_name: str = "documents",
        provider_name: Optional[str] = None,
    ) -> None:
        self.name = provider_name or "sqlite"
        self.database_path = database_path
        self.table_name = table_name
        self._conn: Optional[sqlite3.Connection] = None

    async def initialize(self) -> None:
        if self._conn is not None:
            return

        try:
            self._conn = sqlite3.connect(self.database_path)
            if self._conn is None:
                raise RAGError("Failed to create database connection")

            cursor = self._conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embedding BLOB
                )
                """
            )
            self._conn.commit()
        except Exception as e:
            raise RAGError(f"Failed to initialize SQLite database: {e}") from e

    async def store(self, documents: List[Document]) -> None:
        if not documents:
            return

        if self._conn is None:
            raise RAGError("Database connection not initialized")

        try:
            cursor = self._conn.cursor()
            for doc in documents:
                embedding_bytes = np.array(doc.embedding).tobytes() if doc.embedding else None
                cursor.execute(
                    f"""
                    INSERT OR REPLACE INTO {self.table_name}
                    (id, content, metadata, embedding)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        doc.id,
                        doc.content,
                        str(doc.metadata) if doc.metadata else None,
                        embedding_bytes,
                    ),
                )
            self._conn.commit()
        except Exception as e:
            raise RAGError(f"Failed to store documents: {e}") from e

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        if self._conn is None:
            raise RAGError("Database connection not initialized")

        try:
            cursor = self._conn.cursor()
            query_array = np.array(query_embedding)

            cursor.execute(
                f"SELECT id, content, metadata, embedding FROM {self.table_name} WHERE embedding IS NOT NULL"
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                doc_id, content, metadata_str, embedding_bytes = row
                doc_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

                similarity = np.dot(query_array, doc_embedding) / (
                    np.linalg.norm(query_array) * np.linalg.norm(doc_embedding)
                )

                if filter_metadata:
                    doc_metadata = eval(metadata_str) if metadata_str else {}
                    if not all(
                        doc_metadata.get(k) == v for k, v in filter_metadata.items()
                    ):
                        continue

                results.append(
                    SearchResult(
                        document=Document(
                            id=doc_id,
                            content=content,
                            metadata=eval(metadata_str) if metadata_str else None,
                            embedding=doc_embedding.tolist(),
                        ),
                        score=float(similarity),
                    )
                )

            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]

        except Exception as e:
            raise RAGError(f"Failed to search documents: {e}") from e

    def get_config(self) -> Dict[str, Any]:
        return {
            "database_path": self.database_path,
            "table_name": self.table_name,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "capabilities": ["vector_store", "similarity_search"],
            "supports_metadata_filter": True,
        }