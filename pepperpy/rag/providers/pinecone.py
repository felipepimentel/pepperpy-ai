"""Pinecone provider implementation for RAG capabilities.

This module provides a Pinecone-based implementation of the RAG provider interface,
using Pinecone for persistent vector storage and retrieval.

Example:
    >>> from pepperpy.rag import RAGProvider, Document
    >>> provider = RAGProvider.from_config({
    ...     "provider": "pinecone",
    ...     "api_key": "your-api-key",
    ...     "environment": "us-west1-gcp",
    ...     "index_name": "my-index"
    ... })
    >>> docs = [
    ...     Document("Weather is sunny", {"source": "api"}),
    ...     Document("Temperature is 75°F", {"source": "sensor"})
    ... ]
    >>> provider.add_documents(docs)
    >>> results = provider.retrieve("What's the weather?")
"""

import os
import uuid
from typing import Any, Dict, List, Optional, Sequence

from ..document import Document
from ..provider import RAGError, RAGProvider
from ..query import Query
from ..result import RetrievalResult


class PineconeRAGProvider(RAGProvider):
    """Pinecone implementation of the RAG provider interface.

    This provider uses Pinecone for cloud-based vector storage and retrieval,
    with support for:
    - Multiple embedding models
    - Metadata filtering
    - Namespaced collections
    - Batch operations
    """

    name = "pinecone"

    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        index_name: str = "pepperpy",
        namespace: Optional[str] = None,
        embedding_function: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Pinecone RAG provider.

        Args:
            api_key: Pinecone API key (default: None, uses env var)
            environment: Pinecone environment (default: None, uses env var)
            index_name: Name of the Pinecone index (default: pepperpy)
            namespace: Optional namespace for vectors
            embedding_function: Name of embedding function (default: None, uses sentence-transformers)
            **kwargs: Additional configuration options

        Raises:
            RAGError: If required dependencies are not installed
        """
        try:
            import pinecone
        except ImportError:
            raise RAGError(
                "Pinecone provider requires pinecone-client. "
                "Install with: pip install pinecone-client"
            )

        # Initialize Pinecone client
        pinecone.init(
            api_key=api_key or os.getenv("PINECONE_API_KEY"),
            environment=environment or os.getenv("PINECONE_ENVIRONMENT"),
        )

        # Initialize embedding function
        if embedding_function:
            try:
                from pinecone.embeddings import get_embedding_function

                self.embeddings = get_embedding_function(embedding_function)
            except (ImportError, AttributeError) as e:
                raise RAGError(f"Failed to initialize embedding function: {e}")
        else:
            try:
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer("all-MiniLM-L6-v2")
                self.embeddings = lambda x: model.encode(x).tolist()
            except ImportError:
                raise RAGError(
                    "Default embedding function requires sentence-transformers. "
                    "Install with: pip install sentence-transformers"
                )

        # Get or create index
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=384,  # Default for all-MiniLM-L6-v2
                metric="cosine",
                **kwargs,
            )

        self.index = pinecone.Index(index_name)
        self.namespace = namespace

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

        # Prepare documents for Pinecone
        vectors = []
        for doc in documents:
            doc_id = str(uuid.uuid4())
            if doc.metadata and "id" in doc.metadata:
                doc_id = str(doc.metadata["id"])

            if not doc.embeddings:
                doc.embeddings = self.embeddings(doc.content)

            vectors.append(
                {
                    "id": doc_id,
                    "values": doc.embeddings,
                    "metadata": {
                        "content": doc.content,
                        **(doc.metadata or {}),
                    },
                }
            )

        # Add to index
        self.index.upsert(
            vectors=vectors,
            namespace=self.namespace,
            **kwargs,
        )

    async def remove_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Remove documents from the provider."""
        self.index.delete(
            ids=[str(doc_id) for doc_id in document_ids],
            namespace=self.namespace,
            **kwargs,
        )

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents matching a query."""
        # Get query embeddings
        if not query.embeddings:
            query.embeddings = self.embeddings(query.text)

        # Prepare query parameters
        filter = {}
        if query.metadata:
            filter.update(query.metadata)

        # Search index
        results = self.index.query(
            vector=query.embeddings,
            top_k=limit,
            namespace=self.namespace,
            filter=filter or None,
            include_values=True,
            include_metadata=True,
            **kwargs,
        )

        # Convert results to documents
        documents = []
        scores = []
        for match in results.matches:
            doc = Document(
                content=match.metadata.pop("content"),
                metadata=match.metadata,
                embeddings=match.values,
            )
            documents.append(doc)
            scores.append(float(match.score))

        return RetrievalResult(
            query=query,
            documents=documents,
            scores=scores,
            metadata={
                "total_docs": self.index.describe_index_stats().total_vector_count,
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
            result = self.index.fetch(
                ids=[str(document_id)],
                namespace=self.namespace,
                **kwargs,
            )
            if result.vectors:
                vector = result.vectors[document_id]
                return Document(
                    content=vector.metadata.pop("content"),
                    metadata=vector.metadata,
                    embeddings=vector.values,
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
        # Note: Pinecone doesn't support listing all vectors directly
        # This is a workaround using a zero vector to get all documents
        results = self.index.query(
            vector=[0.0] * 384,  # Zero vector for all-MiniLM-L6-v2
            top_k=limit,
            namespace=self.namespace,
            include_values=True,
            include_metadata=True,
            **kwargs,
        )
        return [
            Document(
                content=match.metadata.pop("content"),
                metadata=match.metadata,
                embeddings=match.values,
            )
            for match in results.matches[offset : offset + limit]
        ]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Pinecone RAG provider capabilities.

        Returns:
            Dictionary of provider capabilities including:
            - cloud_based: True for cloud providers
            - max_docs: Maximum documents per index
            - supports_filters: Whether filtering is supported
            - supports_namespaces: Whether namespaces are supported
            - embedding_function: Current embedding function
            - requires_api_key: Whether API key is required
        """
        return {
            "cloud_based": True,
            "max_docs": 100_000_000,  # Pinecone can handle 100M+ vectors
            "supports_filters": True,
            "supports_namespaces": True,
            "embedding_function": (
                self.embeddings.__name__
                if hasattr(self.embeddings, "__name__")
                else "sentence-transformers"
            ),
            "requires_api_key": True,
            "dimensions": {"all-MiniLM-L6-v2": 384},
        }
