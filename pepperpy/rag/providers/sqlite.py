"""SQLite RAG provider implementation."""

import json
import sqlite3
from typing import Any, Dict, List, Optional, Union

import numpy as np

from ..base import Document, Query, RAGError, RAGProvider, SearchResult


class SQLiteRAGProvider(RAGProvider):
    """SQLite RAG provider.

    This provider stores documents and embeddings in a SQLite database.
    """

    def __init__(
        self,
        database_path: Optional[str] = None,
        embedding_dim: int = 384,
        **kwargs: Any,
    ) -> None:
        """Initialize SQLite RAG provider.

        Args:
            database_path: Path to SQLite database
            embedding_dim: Dimension of the embedding vectors
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.database_path = database_path or ":memory:"
        self.conn: Optional[sqlite3.Connection] = None
        self.embedding_dim = embedding_dim
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self.initialized:
            self.conn = sqlite3.connect(self.database_path)
            if not self.conn:
                raise RAGError("Failed to connect to database")

            # Create documents table if it doesn't exist
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT,
                    embedding BLOB
                )
                """
            )
            self.conn.commit()
            self.initialized = True

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in the RAG context.

        Args:
            docs: Document or list of documents to store.
        """
        if isinstance(docs, Document):
            docs = [docs]

        if not docs:
            return

        if not self.initialized:
            await self.initialize()

        if not self.conn:
            raise RAGError("Database connection not initialized")

        try:
            cursor = self.conn.cursor()
            for doc in docs:
                doc_id = getattr(doc, "id", None) or str(hash(doc.text))
                metadata = doc.metadata or {}

                # Get embedding from _data if available
                embedding = doc.get("embeddings", None)
                if embedding is None:
                    embedding = await self.embed_query(doc.text)

                # Convert embedding to bytes if present
                embedding_bytes = None
                if embedding:
                    embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO documents
                    (id, content, metadata, embedding)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        doc_id,
                        doc.text,
                        json.dumps(metadata) if metadata else None,
                        embedding_bytes,
                    ),
                )
            self.conn.commit()
        except Exception as e:
            raise RAGError(f"Failed to store documents: {e}") from e

    async def search(
        self,
        query: Union[str, Query],
        limit: int = 5,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search documents.

        Args:
            query: Query string or Query object
            limit: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            List of documents
        """
        if isinstance(query, str):
            # Get query embedding
            query_embedding = await self.embed_query(query)
            metadata_filter = kwargs.get("metadata", None)
        elif isinstance(query, Query):
            if query.embeddings is None:
                query_embedding = await self.embed_query(query.text)
            else:
                query_embedding = query.embeddings
            metadata_filter = query.metadata
        else:
            raise ValueError(f"Invalid query type: {type(query)}")

        # Search by embedding
        return await self._search_by_embedding(
            query_embedding=query_embedding,
            top_k=limit,
            filter_metadata=metadata_filter,
        )

    async def _search_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search by embedding."""
        if not self.initialized:
            await self.initialize()

        if not self.conn:
            raise RAGError("Database connection not initialized")

        try:
            cursor = self.conn.cursor()
            query_array = np.array(query_embedding)

            cursor.execute(
                "SELECT id, content, metadata, embedding FROM documents WHERE embedding IS NOT NULL"
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                doc_id, content, metadata_str, embedding_bytes = row
                doc_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

                # Check if dimensions match, if not, skip this document
                if len(doc_embedding) != len(query_array):
                    print(
                        f"Warning: Embedding dimensions don't match. Expected {len(query_array)}, got {len(doc_embedding)}. Skipping document."
                    )
                    continue

                similarity = np.dot(query_array, doc_embedding) / (
                    np.linalg.norm(query_array) * np.linalg.norm(doc_embedding)
                )

                if filter_metadata:
                    doc_metadata = json.loads(metadata_str) if metadata_str else {}
                    if not all(
                        doc_metadata.get(k) == v for k, v in filter_metadata.items()
                    ):
                        continue

                results.append(
                    SearchResult(
                        id=doc_id,
                        text=content,
                        metadata=json.loads(metadata_str) if metadata_str else {},
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
        }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "capabilities": ["vector_store", "similarity_search"],
            "supports_metadata_filter": True,
        }

    async def embed_query(self, text: str) -> List[float]:
        """Embed a query text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Generate random vector for mock implementation
        vector = np.random.randn(self.embedding_dim)
        vector = vector / np.linalg.norm(vector)
        return vector.tolist()

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Ensure we're using the same dimension as embed_query
        return [await self.embed_query(text) for text in texts]

    async def store_documents(self, documents: List[Document]) -> None:
        """Store documents in the RAG context.

        Args:
            documents: List of documents to store.
        """
        await self.store(documents)

    async def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: ID of the document to get

        Returns:
            The document if found, None otherwise
        """
        if not self.initialized:
            raise RAGError("Database connection not initialized")

        if not self.conn:
            raise RAGError("Database connection not initialized")

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT id, content, metadata, embedding FROM documents WHERE id = ?",
                (doc_id,),
            )
            row = cursor.fetchone()

            if row is None:
                return None

            doc_id, content, metadata_str, embedding_bytes = row

            # Convert metadata string to dict if present
            metadata = json.loads(metadata_str) if metadata_str else {}

            # Convert embedding bytes to list if present
            embedding = None
            if embedding_bytes:
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()

            return Document(
                text=content,
                metadata=metadata,
                _data={"embeddings": embedding} if embedding else {},
            )
        except Exception as e:
            raise RAGError(f"Failed to get document {doc_id}: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.conn:
            self.conn.close()
            self.conn = None
        self.initialized = False
