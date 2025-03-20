"""Chroma provider implementation for RAG capabilities.

This module provides a Chroma-based implementation of the RAG provider interface,
using ChromaDB for persistent vector storage and retrieval.
"""

import os
import uuid
from typing import Any, Dict, Optional, Sequence, Union

from pepperpy.rag.provider import (
    Document,
    Query,
    RAGError,
    RAGProvider,
    RetrievalResult,
)


class ChromaRAGProvider(RAGProvider):
    """Chroma implementation of the RAG provider interface using ChromaDB."""

    name = "chroma"

    def __init__(
        self,
        collection_name: str = "pepperpy",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Chroma RAG provider.

        Args:
            collection_name: Name of the ChromaDB collection (default: pepperpy)
            persist_directory: Directory to persist vectors (default: None, in-memory)
            embedding_function: Name of embedding function (default: None, uses sentence-transformers)
            **kwargs: Additional configuration options

        Raises:
            RAGError: If required dependencies are not installed
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise RAGError(
                "Chroma provider requires chromadb. Install with: pip install chromadb"
            )

        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        self.kwargs = kwargs

        try:
            # Initialize ChromaDB client
            settings = Settings()
            if persist_directory:
                os.makedirs(persist_directory, exist_ok=True)
                settings = Settings(
                    persist_directory=persist_directory, is_persistent=True
                )

            self.client = chromadb.Client(settings)

            # Set up embedding function
            if embedding_function is None:
                try:
                    from chromadb.utils.embedding_functions import (
                        SentenceTransformerEmbeddingFunction,
                    )

                    self.embeddings = SentenceTransformerEmbeddingFunction()
                except ImportError:
                    raise RAGError(
                        "Default embedding requires sentence-transformers. "
                        "Install with: pip install sentence-transformers"
                    )
            else:
                # TODO: Support other embedding functions
                raise NotImplementedError(
                    f"Embedding function {embedding_function} not supported yet"
                )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embeddings,
                metadata={"hnsw:space": "cosine"},
            )

        except Exception as e:
            raise RAGError(f"Failed to initialize Chroma: {e}")

    def initialize(self) -> None:
        """Initialize the provider.

        Validates that the client and collection are ready.
        """
        if not hasattr(self, "client") or not hasattr(self, "collection"):
            raise RAGError("Chroma client/collection not properly initialized")

    def add_documents(self, documents: Sequence[Document], **kwargs: Any) -> None:
        """Add documents to the retrieval collection.

        Args:
            documents: Documents to add
            **kwargs: Additional provider-specific arguments

        Raises:
            ValidationError: If documents are invalid
            RAGError: If document addition fails
        """
        try:
            # Prepare document batches
            ids = []
            texts = []
            metadatas = []

            for doc in documents:
                # Generate ID if not provided
                doc_id = doc.metadata.get("id") if doc.metadata else str(uuid.uuid4())
                ids.append(doc_id)
                texts.append(doc.content)
                metadatas.append(doc.metadata or {})

            # Add documents to collection
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas, **kwargs)

        except Exception as e:
            raise RAGError(f"Failed to add documents: {e}")

    def retrieve(self, query: Union[str, Query], **kwargs: Any) -> RetrievalResult:
        """Retrieve relevant documents for a query.

        Args:
            query: Query string or Query object
            **kwargs: Additional provider-specific arguments

        Returns:
            RetrievalResult containing matched documents and scores

        Raises:
            ValidationError: If query is invalid
            RAGError: If retrieval fails
        """
        try:
            # Convert query to Query object if string
            query_obj = query if isinstance(query, Query) else Query(text=query)

            # Prepare query parameters
            where = query_obj.filters or None
            n_results = query_obj.k

            # Query collection
            results = self.collection.query(
                query_texts=[query_obj.text], where=where, n_results=n_results, **kwargs
            )

            # Convert results to documents
            documents = []
            scores = []

            if results["ids"]:
                for doc_id, text, metadata, distance in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    # Convert distance to similarity score (cosine)
                    score = 1.0 - (distance / 2.0)
                    if (
                        query_obj.score_threshold is None
                        or score >= query_obj.score_threshold
                    ):
                        metadata["id"] = doc_id
                        documents.append(Document(content=text, metadata=metadata))
                        scores.append(score)

            return RetrievalResult(
                documents=documents,
                scores=scores,
                metadata={
                    "total_docs": self.collection.count(),
                    "filtered_docs": len(documents),
                    "collection": self.collection_name,
                    "persist_directory": self.persist_directory,
                },
            )

        except Exception as e:
            raise RAGError(f"Failed to retrieve documents: {e}")

    def delete_documents(self, document_ids: Sequence[str], **kwargs: Any) -> None:
        """Delete documents from the retrieval collection.

        Args:
            document_ids: IDs of documents to delete
            **kwargs: Additional provider-specific arguments

        Raises:
            ValidationError: If document IDs are invalid
            RAGError: If document deletion fails
        """
        try:
            self.collection.delete(ids=list(document_ids), **kwargs)
        except Exception as e:
            raise RAGError(f"Failed to delete documents: {e}")

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Chroma RAG provider capabilities."""
        return {
            "persistent": bool(self.persist_directory),
            "max_docs": 1_000_000,  # ChromaDB can handle millions of vectors
            "supports_filters": True,
            "supports_persistence": True,
            "embedding_function": (self.embedding_function or "sentence-transformers"),
        }
