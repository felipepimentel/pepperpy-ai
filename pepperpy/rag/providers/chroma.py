"""Chroma provider implementation for RAG capabilities.

This module provides a Chroma-based implementation of the RAG provider interface,
using ChromaDB for persistent vector storage and retrieval.
"""

import uuid
from typing import Any, Dict, List, Optional, Sequence

from ..document import Document
from ..provider import RAGError, RAGProvider
from ..query import Query
from ..result import RetrievalResult


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

        # Store persist_directory for capabilities
        self.persist_directory = persist_directory

        # Initialize ChromaDB client
        settings = Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False,
            **kwargs,
        )
        self.client = chromadb.Client(settings)

        # Initialize embedding function
        if embedding_function:
            try:
                from chromadb.utils import embedding_functions

                self.embeddings = getattr(embedding_functions, embedding_function)()
            except (ImportError, AttributeError) as e:
                raise RAGError(f"Failed to initialize embedding function: {e}")
        else:
            try:
                from chromadb.utils.embedding_functions import (
                    SentenceTransformerEmbeddingFunction,
                )

                self.embeddings = SentenceTransformerEmbeddingFunction()
            except ImportError:
                raise RAGError(
                    "Default embedding function requires sentence-transformers. "
                    "Install with: pip install sentence-transformers"
                )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embeddings,
            metadata={"hnsw:space": "cosine"},
        )

    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    async def shutdown(self) -> None:
        """Shut down the provider."""
        pass

    async def add_documents(
        self,
        documents: Sequence[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the provider."""
        if not documents:
            return

        # Prepare documents for ChromaDB
        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for doc in documents:
            doc_id = str(uuid.uuid4())
            if doc.metadata and "id" in doc.metadata:
                doc_id = str(doc.metadata["id"])

            ids.append(doc_id)
            texts.append(doc.content)
            metadatas.append(doc.metadata or {})
            if doc.embeddings:
                embeddings.append(doc.embeddings)

        # Add to collection
        if embeddings and len(embeddings) == len(documents):
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings,
                **kwargs,
            )
        else:
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                **kwargs,
            )

    async def remove_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Remove documents from the provider."""
        self.collection.delete(ids=[str(doc_id) for doc_id in document_ids], **kwargs)

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents matching a query."""
        # Prepare query parameters
        where = {}
        if query.metadata:
            where.update(query.metadata)

        # Search collection
        results = self.collection.query(
            query_texts=[query.text],
            n_results=limit,
            where=where or None,
            **kwargs,
        )

        # Convert results to documents
        documents = []
        scores = []
        for i in range(len(results["ids"][0])):
            doc = Document(
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                embeddings=results["embeddings"][0][i]
                if "embeddings" in results
                else None,
            )
            documents.append(doc)
            scores.append(float(results["distances"][0][i]))

        return RetrievalResult(
            query=query,
            documents=documents,
            scores=scores,
            metadata={
                "total_docs": self.collection.count(),
                "filtered_docs": len(documents),
            },
        )

    async def get_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Document]:
        """Get a document by ID."""
        try:
            result = self.collection.get(ids=[str(document_id)], **kwargs)
            if result["ids"]:
                return Document(
                    content=result["documents"][0],
                    metadata=result["metadatas"][0],
                    embeddings=result["embeddings"][0]
                    if "embeddings" in result
                    else None,
                )
        except Exception:
            pass
        return None

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Document]:
        """List documents in the provider."""
        results = self.collection.get(
            limit=limit,
            offset=offset,
            **kwargs,
        )
        return [
            Document(
                content=doc,
                metadata=meta,
                embeddings=emb if "embeddings" in results else None,
            )
            for doc, meta, emb in zip(
                results["documents"],
                results["metadatas"],
                results.get("embeddings", [None] * len(results["documents"])),
            )
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Chroma RAG provider capabilities."""
        return {
            "persistent": bool(self.persist_directory),
            "max_docs": 1_000_000,  # ChromaDB can handle millions of vectors
            "supports_filters": True,
            "supports_persistence": True,
            "embedding_function": (
                self.embeddings.__class__.__name__
                if self.embeddings
                else "sentence-transformers"
            ),
        }
