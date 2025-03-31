"""ChromaDB provider implementation for RAG capabilities.

This module provides a ChromaDB-based implementation of the RAG provider interface,
supporting persistent vector storage, similarity search, and metadata filtering.

Example:
    >>> from pepperpy import PepperPy
    >>>
    >>> # Initialize PepperPy with RAG (automatically configures embeddings)
    >>> pepperpy = PepperPy().with_rag()
    >>>
    >>> # Or explicitly configure providers
    >>> pepperpy = (
    ...     PepperPy()
    ...     .with_embeddings()  # Uses PEPPERPY_EMBEDDINGS__PROVIDER from .env
    ...     .with_rag()  # Uses PEPPERPY_RAG__PROVIDER from .env
    ... )
    >>>
    >>> # Add documents and search
    >>> async with pepperpy:
    ...     await pepperpy.rag.store([
    ...         Document(text="Example document", metadata={"source": "test"})
    ...     ])
    ...     results = await pepperpy.rag.search("query", top_k=3)
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings

from pepperpy.core.base import ValidationError
from pepperpy.core.utils import lazy_provider_class
from pepperpy.embeddings.base import EmbeddingProvider
from pepperpy.rag.base import Document, Query, RAGProvider, SearchResult

logger = logging.getLogger(__name__)


class ChromaEmbeddingFunction(EmbeddingFunction):
    """Embedding function for ChromaDB using PepperPy embedding provider."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        """Initialize embedding function.

        Args:
            provider: PepperPy embedding provider
        """
        self.provider = provider

    def __call__(self, input: Documents) -> Embeddings:
        """Generate embeddings for texts.

        Args:
            input: List of texts to embed

        Returns:
            List of embeddings
        """
        if not isinstance(input, list):
            input = [input]

        # Use synchronous embedding method
        model = self.provider._get_embedding_function()
        embeddings = model.encode(input)
        return embeddings.tolist()


@lazy_provider_class("rag", "chroma")
class ChromaProvider(RAGProvider):
    """ChromaDB provider implementation."""

    name = "chroma"

    
    # Attributes auto-bound from plugin.yaml com valores padrão como fallback
    api_key: str
    client: Optional[httpx.AsyncClient] = None
def __init__(
        self,
        collection_name: str = "default",
        persist_directory: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize ChromaDB provider.

        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist data
            embedding_provider: Provider for generating embeddings
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_provider = embedding_provider
        self.client = None
        self._collection: Optional[Collection] = None

    def get_collection(self) -> Collection:
        """Get the ChromaDB collection.

        Returns:
            ChromaDB collection

        Raises:
            ValidationError: If collection is not initialized
        """
        if not self._collection:
            raise ValidationError("Collection not initialized")
        return self._collection

    async def initialize(self) -> None:
        """Initialize the provider."""
        # Initialize ChromaDB client
        settings = Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False,
            is_persistent=self.persist_directory is not None,
        )
        self.client = chromadb.Client(settings)

        # Initialize embedding function
        embedding_fn = ChromaEmbeddingFunction(self.embedding_provider)

        # Get or create collection
        self._collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=embedding_fn,
        )

    async def cleanup(self) -> None:
        """Clean up resources."""
        # No cleanup needed for ChromaDB
        pass

    def _get_metadata(self, doc: Document) -> Dict[str, Any]:
        """Get metadata for document.

        Args:
            doc: Document to get metadata for

        Returns:
            Metadata dictionary
        """
        metadata = doc.metadata.copy() if doc.metadata else {}
        if not metadata:
            metadata["id"] = doc.get("id", "")
        return metadata

    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in ChromaDB.

        Args:
            docs: Document or list of documents to store

        Raises:
            ValidationError: If collection is not initialized
        """
        collection = self.get_collection()

        if isinstance(docs, Document):
            docs = [docs]

        # Prepare documents for ChromaDB
        texts = [doc.text for doc in docs]
        metadatas = [self._get_metadata(doc) for doc in docs]
        ids = [str(i) for i in range(len(docs))]

        # Add documents to collection
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )

    async def search(
        self,
        query: Union[str, Query],
        limit: int = 5,
        **kwargs: Any,
    ) -> Sequence[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query text or Query object
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results

        Raises:
            ValidationError: If collection is not initialized
        """
        collection = self.get_collection()

        # Get query text
        query_text = query.text if isinstance(query, Query) else query

        # Search collection
        results = collection.query(
            query_texts=[query_text],
            n_results=limit,
            **kwargs,
        )

        # Convert results to SearchResult objects
        search_results = []
        for i, (doc_id, text, metadata, distance) in enumerate(
            zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ):
            search_results.append(
                SearchResult(
                    id=doc_id,
                    text=text,
                    metadata=metadata,
                    score=1.0 - distance,  # Convert distance to similarity score
                )
            )

        return search_results

    async def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: ID of the document to get

        Returns:
            The document if found, None otherwise

        Raises:
            ValidationError: If collection is not initialized
        """
        collection = self.get_collection()

        try:
            result = collection.get(ids=[doc_id])
            if not result["documents"]:
                return None

            return Document(
                text=result["documents"][0],
                metadata=result["metadatas"][0] if result["metadatas"] else {},
            )
        except Exception:
            return None

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration.

        Returns:
            Provider configuration
        """
        return {
            "persist_directory": self.persist_directory,
            "collection_name": self.collection_name,
            "has_embedding_function": self.embedding_provider is not None,
        }

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the provider capabilities.

        Returns:
            A dictionary of provider capabilities
        """
        return {
            "supports_persistence": True,
            "supports_metadata_filtering": True,
            "supports_batch_operations": True,
            "supports_custom_embeddings": True,
            "max_batch_size": 1000,
            "max_dimensions": 1536,
        }

    async def delete_documents(
        self,
        document_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> None:
        """Delete documents from the collection.

        Args:
            document_ids: Document ID(s) to delete
            **kwargs: Additional deletion options
        """
        collection = self.get_collection()

        if isinstance(document_ids, str):
            document_ids = [document_ids]

        collection.delete(ids=document_ids)

    async def get_documents(
        self,
        document_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Get documents by ID.

        Args:
            document_ids: Document ID(s) to retrieve
            **kwargs: Additional retrieval options

        Returns:
            List of document data
        """
        collection = self.get_collection()

        if isinstance(document_ids, str):
            document_ids = [document_ids]

        results = collection.get(ids=document_ids)
        documents = []
        for i, doc_id in enumerate(results["ids"]):
            documents.append({
                "id": doc_id,
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        return documents

    async def list_documents(
        self,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List all documents in the collection.

        Args:
            **kwargs: Additional listing options

        Returns:
            List of document data
        """
        collection = self.get_collection()
        results = collection.get()
        documents = []
        for i, doc_id in enumerate(results["ids"]):
            documents.append({
                "id": doc_id,
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        return documents

    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection.

        Args:
            **kwargs: Additional deletion options
        """
        if self.client and self._collection:
            self.client.delete_collection(self.collection_name)
            self._collection = None

    async def count_documents(self, **kwargs: Any) -> int:
        """Count documents in the collection.

        Args:
            **kwargs: Additional counting options

        Returns:
            Number of documents
        """
        collection = self.get_collection()
        return collection.count()

    async def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics.

        Returns:
            Provider statistics
        """
        return {
            "document_count": await self.count_documents(),
            "collection_name": self.collection_name,
            "has_persistence": self.persist_directory is not None,
        }
