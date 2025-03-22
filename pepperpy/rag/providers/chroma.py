"""Chroma provider implementation for RAG capabilities.

This module provides a Chroma-based implementation of the RAG provider interface,
using ChromaDB for persistent vector storage and retrieval.
"""

import hashlib
import uuid
from typing import Any, Dict, List, Optional, Sequence, Union, cast

from chromadb.api.types import (
    Documents,
    Embedding,
    EmbeddingFunction,
    Embeddings,
    GetResult,
    Metadata,
    QueryResult,
)

from ..document import Document
from ..provider import RAGError, RAGProvider
from ..query import Query
from ..result import RetrievalResult


def _to_dict(metadata: Optional[Metadata]) -> Dict[str, Any]:
    """Convert metadata to dictionary."""
    if metadata is None:
        return {}
    return {k: v for k, v in metadata.items()}


def _to_embedding(embedding: Optional[Union[Embedding, List[float]]]) -> Optional[List[float]]:
    """Convert embedding to list of floats."""
    if embedding is None:
        return None
    if isinstance(embedding, list):
        return embedding
    return list(embedding)


def _get_embeddings(result: Union[GetResult, QueryResult]) -> Optional[List[Embedding]]:
    """Get embeddings from result."""
    if "embeddings" not in result:
        return None
    embeddings = result.get("embeddings")
    if not embeddings:
        return None
    return embeddings


class HashEmbeddingFunction(EmbeddingFunction):
    """Simple embedding function that uses SHA-256 hash for testing purposes."""

    def __init__(self, dimension: int = 64) -> None:
        """Initialize the hash embedding function.

        Args:
            dimension: Size of the embedding vector (default: 64)
        """
        self.dimension = dimension

    def __call__(self, texts: Documents) -> Embeddings:
        """Convert texts to embeddings using SHA-256 hash.

        Args:
            texts: List of texts to convert to embeddings

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            # Get SHA-256 hash of text
            hash_bytes = hashlib.sha256(str(text).encode()).digest()
            
            # Convert hash bytes to floats between -1 and 1
            embedding = []
            for i in range(self.dimension):
                byte_val = hash_bytes[i % 32]  # Reuse hash bytes if needed
                embedding.append((byte_val / 128.0) - 1.0)  # Scale to [-1, 1]
            
            embeddings.append(embedding)
        return embeddings


class ChromaRAGProvider(RAGProvider):
    """Chroma implementation of the RAG provider interface using ChromaDB."""

    name = "chroma"

    def __init__(
        self,
        collection_name: str = "pepperpy",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Union[str, EmbeddingFunction]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Chroma RAG provider.

        Args:
            collection_name: Name of the ChromaDB collection (default: pepperpy)
            persist_directory: Directory to persist vectors (default: None, in-memory)
            embedding_function: Name or instance of embedding function (default: None, uses hash-based)
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
        if isinstance(embedding_function, str):
            try:
                from chromadb.utils import embedding_functions

                self.embeddings = getattr(embedding_functions, embedding_function)()
            except (ImportError, AttributeError) as e:
                raise RAGError(f"Failed to initialize embedding function: {e}")
        elif isinstance(embedding_function, EmbeddingFunction):
            self.embeddings = embedding_function
        else:
            # Use simple hash-based embeddings by default
            self.embeddings = HashEmbeddingFunction()

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
            metadatas.append(cast(Metadata, doc.metadata or {}))
            if doc.embeddings:
                embeddings.append(cast(Embedding, doc.embeddings))

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
        results: QueryResult = self.collection.query(
            query_texts=[query.text],
            n_results=limit,
            where=where or None,
            **kwargs,
        )

        # Convert results to documents
        documents = []
        scores = []
        if results["ids"] and results["ids"][0]:
            embeddings = _get_embeddings(results)
            for i in range(len(results["ids"][0])):
                doc = Document(
                    content=results["documents"][0][i],
                    metadata=_to_dict(results["metadatas"][0][i]),
                    embeddings=_to_embedding(
                        embeddings[0][i] if embeddings else None
                    ),
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
            result: GetResult = self.collection.get(ids=[str(document_id)], **kwargs)
            if result["ids"] and result["ids"][0]:
                embeddings = _get_embeddings(result)
                return Document(
                    content=result["documents"][0],
                    metadata=_to_dict(result["metadatas"][0]),
                    embeddings=_to_embedding(
                        embeddings[0] if embeddings else None
                    ),
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
        results: GetResult = self.collection.get(
            limit=limit,
            offset=offset,
            **kwargs,
        )
        if not results["ids"]:
            return []

        embeddings = _get_embeddings(results)
        return [
            Document(
                content=doc,
                metadata=_to_dict(meta),
                embeddings=_to_embedding(
                    emb if embeddings else None
                ),
            )
            for doc, meta, emb in zip(
                results["documents"],
                results["metadatas"],
                embeddings or [None] * len(results["documents"]),
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
                else "hash-based"
            ),
        }
