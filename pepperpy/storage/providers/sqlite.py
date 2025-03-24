"""SQLite RAG provider implementation.

This module provides a simple RAG provider implementation using SQLite
for vector storage and scikit-learn for similarity search.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..document import Document
from ..provider import RAGError
from ..query import Query
from ..result import RetrievalResult


class SQLiteRAGProvider:
    """Simple RAG provider using SQLite for vector storage.

    This provider is designed for simplicity and ease of use, suitable for
    small to medium datasets. It uses SQLite for storage and scikit-learn
    for vector similarity search.

    Args:
        data_dir: Directory to store SQLite database
        **kwargs: Additional configuration options
    """

    def __init__(
        self,
        data_dir: str = ".pepperpy/sqlite",
        **kwargs: Any,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "vectors.db"
        self.conn = None
        self.documents: Dict[str, Document] = {}

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates data directory and SQLite database if they don't exist.
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)

            # Initialize SQLite database
            self.conn = sqlite3.connect(str(self.db_path))
            cursor = self.conn.cursor()

            # Create tables if they don't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embeddings TEXT,
                    created_at TEXT
                )
            """
            )

            # Load existing documents
            cursor.execute("SELECT * FROM documents")
            for row in cursor.fetchall():
                doc_id, content, metadata_str, embeddings_str, created_at = row
                doc = Document(
                    content=content,
                    metadata=json.loads(metadata_str) if metadata_str else {},
                    embeddings=json.loads(embeddings_str) if embeddings_str else None,
                    id=doc_id,
                    created_at=created_at,
                )
                self.documents[doc_id] = doc

            self.conn.commit()

        except Exception as e:
            raise RAGError(f"Failed to initialize SQLiteRAGProvider: {str(e)}") from e

    async def shutdown(self) -> None:
        """Shut down the provider.

        Closes SQLite connection.
        """
        try:
            if self.conn:
                self.conn.close()
                self.conn = None

        except Exception as e:
            raise RAGError(f"Failed to shutdown SQLiteRAGProvider: {str(e)}") from e

    async def add_documents(
        self,
        documents: List[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the provider.

        Args:
            documents: List of documents to add
            **kwargs: Additional arguments (unused)

        Raises:
            RAGError: If adding documents fails
        """
        try:
            if not self.conn:
                raise RAGError("Provider not initialized")

            cursor = self.conn.cursor()

            for doc in documents:
                if doc.id is None:
                    continue

                if doc.id in self.documents:
                    continue

                if doc.embeddings is None:
                    raise RAGError(f"Document {doc.id} has no embeddings")

                # Store in SQLite
                cursor.execute(
                    "INSERT INTO documents VALUES (?, ?, ?, ?, ?)",
                    (
                        doc.id,
                        doc.content,
                        json.dumps(doc.metadata),
                        json.dumps(doc.embeddings),
                        doc.created_at.isoformat(),
                    ),
                )

                # Update in-memory cache
                self.documents[doc.id] = doc

            self.conn.commit()

        except Exception as e:
            raise RAGError(f"Failed to add documents: {str(e)}") from e

    async def remove_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Remove documents from the provider.

        Args:
            document_ids: IDs of documents to remove
            **kwargs: Additional arguments (unused)
        """
        try:
            if not self.conn:
                raise RAGError("Provider not initialized")

            cursor = self.conn.cursor()

            # Remove from SQLite
            placeholders = ",".join("?" * len(document_ids))
            cursor.execute(
                f"DELETE FROM documents WHERE id IN ({placeholders})", document_ids
            )

            # Remove from in-memory cache
            for doc_id in document_ids:
                self.documents.pop(doc_id, None)

            self.conn.commit()

        except Exception as e:
            raise RAGError(f"Failed to remove documents: {str(e)}") from e

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents matching a query.

        Args:
            query: Query to search for
            limit: Maximum number of results to return
            **kwargs: Additional arguments (unused)

        Returns:
            Search results with documents and scores

        Raises:
            RAGError: If search fails
        """
        try:
            if not self.conn:
                raise RAGError("Provider not initialized")

            if query.embeddings is None:
                raise RAGError("Query has no embeddings")

            if not self.documents:
                return RetrievalResult(documents=[], scores=[])

            # Get all document embeddings
            doc_embeddings = []
            doc_ids = []

            for doc_id, doc in self.documents.items():
                if doc.embeddings is not None:
                    doc_embeddings.append(doc.embeddings)
                    doc_ids.append(doc_id)

            if not doc_embeddings:
                return RetrievalResult(documents=[], scores=[])

            # Convert to numpy arrays
            query_array = np.array([query.embeddings])
            docs_array = np.array(doc_embeddings)

            # Calculate cosine similarities
            similarities = cosine_similarity(query_array, docs_array)[0]

            # Get top k results
            top_indices = np.argsort(similarities)[-limit:][::-1]

            # Convert to documents and scores
            docs = []
            scores = []

            for idx in top_indices:
                doc_id = doc_ids[idx]
                doc = self.documents.get(doc_id)
                if doc:
                    docs.append(doc)
                    scores.append(float(similarities[idx]))

            return RetrievalResult(documents=docs, scores=scores)

        except Exception as e:
            raise RAGError(f"Failed to search: {str(e)}") from e

    async def get_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: ID of document to get
            **kwargs: Additional arguments (unused)

        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(document_id)

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Document]:
        """List documents in the provider.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            **kwargs: Additional arguments (unused)

        Returns:
            List of documents
        """
        docs = list(self.documents.values())
        return docs[offset : offset + limit]
