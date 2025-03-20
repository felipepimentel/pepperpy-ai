"""Pinecone provider implementation for RAG capabilities.

This module provides a Pinecone-based implementation of the RAG provider interface,
using Pinecone for cloud-based vector storage and retrieval.

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

import uuid
from typing import Any, Dict, Optional, Sequence, Union

from pepperpy.core.validation import ValidationError

from ...internal.provider import Document, Query, RAGError, RAGProvider, RetrievalResult


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
        api_key: str,
        environment: str,
        index_name: str,
        namespace: Optional[str] = None,
        embedding_function: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Pinecone RAG provider.

        Args:
            api_key: Pinecone API key
            environment: Pinecone environment (e.g., us-west1-gcp)
            index_name: Name of the Pinecone index
            namespace: Optional namespace within the index
            embedding_function: Name of embedding function (default: None, uses sentence-transformers)
            **kwargs: Additional configuration options

        Raises:
            RAGError: If required dependencies are not installed
            ValidationError: If configuration is invalid
        """
        try:
            import pinecone
        except ImportError:
            raise RAGError(
                "Pinecone provider requires pinecone-client. "
                "Install with: pip install pinecone-client"
            )

        if not api_key:
            raise ValidationError("Pinecone API key is required")
        if not environment:
            raise ValidationError("Pinecone environment is required")
        if not index_name:
            raise ValidationError("Pinecone index name is required")

        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.namespace = namespace
        self.embedding_function = embedding_function
        self.kwargs = kwargs

        try:
            # Initialize Pinecone client
            pinecone.init(api_key=api_key, environment=environment)

            # Get or create index
            if index_name not in pinecone.list_indexes():
                raise RAGError(
                    f"Index {index_name} does not exist. "
                    "Please create it first in the Pinecone console."
                )

            self.index = pinecone.Index(index_name)

            # Set up embedding function
            if embedding_function is None:
                try:
                    from sentence_transformers import SentenceTransformer

                    self.model = SentenceTransformer("all-MiniLM-L6-v2")
                except ImportError:
                    raise RAGError(
                        "Default embedding requires sentence-transformers. "
                        "Install with: pip install sentence-transformers"
                    )
            else:
                # TODO[v2.0]: Support other embedding functions
                raise NotImplementedError(
                    f"Embedding function {embedding_function} not supported yet"
                )

        except Exception as e:
            raise RAGError(f"Failed to initialize Pinecone: {e}")

    def initialize(self) -> None:
        """Initialize the provider.

        Validates that the index and embedding model are ready.

        Raises:
            RAGError: If provider is not properly initialized
        """
        if not hasattr(self, "index") or not hasattr(self, "model"):
            raise RAGError("Pinecone index/model not properly initialized")

    def add_documents(self, documents: Sequence[Document], **kwargs: Any) -> None:
        """Add documents to the retrieval collection.

        Args:
            documents: Documents to add
            **kwargs: Additional provider-specific arguments
                - batch_size: Number of documents per batch (default: 100)

        Raises:
            ValidationError: If documents are invalid
            RAGError: If document addition fails
        """
        try:
            # Generate embeddings for documents
            texts = [doc.content for doc in documents]
            embeddings = self.model.encode(texts)

            # Prepare document batches
            vectors = []
            for doc, embedding in zip(documents, embeddings):
                # Generate ID if not provided
                doc_id = doc.metadata.get("id") if doc.metadata else str(uuid.uuid4())
                vectors.append({
                    "id": doc_id,
                    "values": embedding.tolist(),
                    "metadata": {"text": doc.content, **(doc.metadata or {})},
                })

            # Upsert vectors in batches
            batch_size = kwargs.get("batch_size", 100)
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self.index.upsert(vectors=batch, namespace=self.namespace, **kwargs)

        except Exception as e:
            raise RAGError(f"Failed to add documents: {e}")

    def retrieve(self, query: Union[str, Query], **kwargs: Any) -> RetrievalResult:
        """Retrieve relevant documents for a query.

        Args:
            query: Query string or Query object
            **kwargs: Additional provider-specific arguments
                - include_values: Include vector values in response
                - sparse_vector: Optional sparse vector for hybrid search

        Returns:
            RetrievalResult containing matched documents and scores

        Raises:
            ValidationError: If query is invalid
            RAGError: If retrieval fails
        """
        try:
            # Convert query to Query object if string
            if isinstance(query, str):
                query = Query(text=query)

            # Generate query embedding
            query_embedding = self.model.encode(query.text)

            # Prepare query parameters
            filter = {}
            if query.filters:
                filter = {k: {"$eq": v} for k, v in query.filters.items()}

            # Query index
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=query.k,
                namespace=self.namespace,
                filter=filter or None,
                include_metadata=True,
                **kwargs,
            )

            # Convert results to documents
            documents = []
            scores = []

            for match in results.matches:
                score = float(match.score)
                if query.score_threshold is None or score >= query.score_threshold:
                    metadata = dict(match.metadata)
                    text = metadata.pop("text")
                    metadata["id"] = match.id
                    documents.append(Document(content=text, metadata=metadata))
                    scores.append(score)

            return RetrievalResult(
                documents=documents,
                scores=scores,
                metadata={
                    "filtered_docs": len(documents),
                    "index": self.index_name,
                    "namespace": self.namespace,
                    "environment": self.environment,
                },
            )

        except Exception as e:
            raise RAGError(f"Failed to retrieve documents: {e}")

    def delete_documents(self, document_ids: Sequence[str], **kwargs: Any) -> None:
        """Delete documents from the retrieval collection.

        Args:
            document_ids: IDs of documents to delete
            **kwargs: Additional provider-specific arguments
                - delete_all: Delete all documents in namespace

        Raises:
            ValidationError: If document IDs are invalid
            RAGError: If document deletion fails
        """
        try:
            if kwargs.get("delete_all"):
                self.index.delete(delete_all=True, namespace=self.namespace, **kwargs)
            else:
                self.index.delete(
                    ids=list(document_ids), namespace=self.namespace, **kwargs
                )
        except Exception as e:
            raise RAGError(f"Failed to delete documents: {e}")

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
            "embedding_function": (self.embedding_function or "sentence-transformers"),
            "requires_api_key": True,
            "dimensions": {"all-MiniLM-L6-v2": 384},
        }
