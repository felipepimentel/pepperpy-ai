"""Annoy RAG provider implementation.

This module provides a lightweight RAG provider implementation using Annoy
(Approximate Nearest Neighbors Oh Yeah) for vector similarity search.
"""

import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from annoy import AnnoyIndex

from ..base import Document, Query, RAGProvider
from ..provider import RAGError

# Valid metric types for Annoy
ANNOY_METRICS = Literal["angular", "euclidean", "manhattan", "hamming", "dot"]


class AnnoyRAGProvider(RAGProvider):
    """Lightweight RAG provider using Annoy for vector similarity search.

    This provider is designed to be lightweight and efficient for most use cases.
    It uses Annoy for approximate nearest neighbor search and local file storage
    for document persistence.

    Args:
        data_dir: Directory to store index and document data
        embedding_dim: Dimension of the embeddings
        n_trees: Number of trees for Annoy index (more = better recall but slower)
        metric: Distance metric to use ('angular', 'euclidean', 'manhattan', 'hamming')
        **kwargs: Additional configuration options
    """

    def __init__(
        self,
        data_dir: str = ".pepperpy/annoy",
        embedding_dim: int = 1536,  # Default for OpenAI embeddings
        n_trees: int = 10,
        metric: ANNOY_METRICS = "angular",
        **kwargs: Any,
    ) -> None:
        super().__init__(name="annoy", config=kwargs)
        self.data_dir = Path(data_dir)
        self.embedding_dim = embedding_dim
        self.n_trees = n_trees
        self.metric: ANNOY_METRICS = metric

        # Paths for storing data
        self.index_path = self.data_dir / "annoy.index"
        self.docs_path = self.data_dir / "documents.pkl"

        # Initialize empty state
        self.index = None
        self.documents: Dict[str, Document] = {}
        self.doc_id_to_idx: Dict[str, int] = {}
        self.idx_to_doc_id: Dict[int, str] = {}
        self.next_idx = 0

    async def initialize(self) -> None:
        """Initialize the provider.

        Creates data directory and loads existing data if available.
        """
        try:
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)

            # Load existing documents if available
            if self.docs_path.exists():
                with open(self.docs_path, "rb") as f:
                    saved_data = pickle.load(f)
                    self.documents = saved_data["documents"]
                    self.doc_id_to_idx = saved_data["doc_id_to_idx"]
                    self.idx_to_doc_id = saved_data["idx_to_doc_id"]
                    self.next_idx = saved_data["next_idx"]

            # Initialize or load Annoy index
            self.index = AnnoyIndex(self.embedding_dim, self.metric)
            if self.index_path.exists():
                self.index.load(str(self.index_path))

        except Exception as e:
            raise RAGError(f"Failed to initialize AnnoyRAGProvider: {str(e)}") from e

    async def cleanup(self) -> None:
        """Clean up resources.

        Saves current state to disk.
        """
        try:
            if self.index and len(self.documents) > 0:
                # Save Annoy index
                self.index.save(str(self.index_path))

                # Save documents and mappings
                with open(self.docs_path, "wb") as f:
                    pickle.dump(
                        {
                            "documents": self.documents,
                            "doc_id_to_idx": self.doc_id_to_idx,
                            "idx_to_doc_id": self.idx_to_doc_id,
                            "next_idx": self.next_idx,
                        },
                        f,
                    )

        except Exception as e:
            raise RAGError(f"Failed to cleanup AnnoyRAGProvider: {str(e)}") from e

    async def store(self, documents: List[Document]) -> None:
        """Store documents in the RAG context.

        Args:
            documents: List of documents to store.

        Raises:
            RAGError: If storing documents fails
        """
        try:
            # Create new index if needed
            if self.index is None:
                self.index = AnnoyIndex(self.embedding_dim, self.metric)

            # Add each document
            for doc in documents:
                if doc.id is None:
                    continue

                if doc.id in self.documents:
                    continue

                if doc.embeddings is None:
                    raise RAGError(f"Document {doc.id} has no embeddings")

                # Add to index
                self.index.add_item(self.next_idx, doc.embeddings)

                # Update mappings
                self.documents[doc.id] = doc
                self.doc_id_to_idx[doc.id] = self.next_idx
                self.idx_to_doc_id[self.next_idx] = doc.id
                self.next_idx += 1

            # Build index if documents were added
            if documents:
                self.index.build(self.n_trees)

        except Exception as e:
            raise RAGError(f"Failed to store documents: {str(e)}") from e

    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query.

        Returns:
            List of relevant documents.

        Raises:
            RAGError: If search fails
        """
        try:
            if not self.index:
                return []

            if query.embeddings is None:
                raise RAGError("Query has no embeddings")

            # Get nearest neighbors
            indices, distances = self.index.get_nns_by_vector(
                query.embeddings, 10, include_distances=True
            )

            # Convert to documents
            docs = []
            for idx in indices:
                doc_id = self.idx_to_doc_id.get(idx)
                if doc_id:
                    doc = self.documents.get(doc_id)
                    if doc:
                        docs.append(doc)

            return docs

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
