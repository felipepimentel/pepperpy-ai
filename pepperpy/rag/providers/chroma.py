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
import os
import uuid
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.base import ProviderError
from pepperpy.core.utils import import_provider, lazy_provider_class
from pepperpy.rag.base import Document, Query, RAGProvider

logger = logging.getLogger(__name__)


@lazy_provider_class("rag", "chroma")
class ChromaProvider(RAGProvider):
    """ChromaDB implementation of the RAG provider interface.

    This provider supports:
    - Persistent vector storage
    - Similarity search
    - Metadata filtering
    - Batch operations
    """

    name = "chroma"

    def __init__(
        self,
        path: Optional[str] = None,
        collection_name: str = "pepperpy",
        embedding_function: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize ChromaDB provider.

        Args:
            path: Path to ChromaDB persistence directory
            collection_name: Name of the collection to use
            embedding_function: Optional custom embedding function to use for vectors
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.path = path
        self.collection_name = collection_name
        self._embedding_function = embedding_function
        self.client = None
        self._collection: Optional[Any] = None

    @property
    def collection(self) -> Any:
        """Get the ChromaDB collection.

        Returns:
            The ChromaDB collection

        Raises:
            ProviderError: If provider is not initialized
        """
        if self._collection is None:
            raise ProviderError(
                "ChromaProvider not initialized. Call initialize() first."
            )
        return self._collection

    async def initialize(self) -> None:
        """Initialize the provider.

        This method sets up the ChromaDB client and collection.

        Raises:
            ProviderError: If no embedding function is provided
        """
        # Import chromadb only when provider is instantiated
        chromadb = import_provider("chromadb", "rag", "chroma")

        # Initialize client with persistence if path provided
        if self.path:
            os.makedirs(self.path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.path)
        else:
            self.client = chromadb.Client()

        if not self._embedding_function:
            raise ProviderError(
                "No embedding function provided. Please provide an embedding function "
                "through the embedding_function parameter."
            )

        # Get or create collection
        self._collection = self.client.get_or_create_collection(
            name=self.collection_name, embedding_function=self._embedding_function
        )

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "path": self.path,
            "collection_name": self.collection_name,
            "has_embedding_function": self._embedding_function is not None,
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

    async def store(self, documents: List[Document]) -> None:
        """Store documents in the collection.

        Args:
            documents: List of documents to store
        """
        # Convert documents to ChromaDB format
        ids = []
        texts = []
        metadatas = []
        embeddings = []

        for doc in documents:
            doc_id = doc.get("id")
            if not doc_id:
                doc_id = str(uuid.uuid4())
                doc["id"] = doc_id
            ids.append(doc_id)
            texts.append(doc.text)
            metadatas.append(doc.metadata)
            if "embeddings" in doc._data:
                embeddings.append(doc._data["embeddings"])

        # Add documents to collection
        if embeddings:
            self.collection.add(
                ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings
            )
        else:
            self.collection.add(ids=ids, documents=texts, metadatas=metadatas)

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> List[Document]:
        """Search for documents similar to query.

        Args:
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional search options

        Returns:
            List of relevant documents
        """
        # Convert query to text
        query_text = query.text

        # Get results from ChromaDB
        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit,
            **kwargs,
        )

        # Convert results to documents
        documents = []
        for i, doc_id in enumerate(results["ids"][0]):
            doc = Document(
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
            )
            doc["id"] = doc_id
            if "distances" in results:
                doc["score"] = 1.0 - results["distances"][0][i]
            documents.append(doc)

        return documents

    async def delete_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Delete documents from the collection.

        Args:
            document_ids: List of document IDs to delete
            **kwargs: Additional deletion options
        """
        self.collection.delete(ids=document_ids)

    async def get_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get a document by ID.

        Args:
            document_id: Document ID to retrieve
            collection_name: Optional collection name
            **kwargs: Additional retrieval options

        Returns:
            Document data if found, None otherwise
        """
        results = self.collection.get(ids=[document_id])
        if not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "text": results["documents"][0],
            "metadata": results["metadatas"][0],
        }

    async def get_documents(
        self,
        document_ids: Union[str, List[str]],
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Get multiple documents by ID.

        Args:
            document_ids: Document ID(s) to retrieve
            collection_name: Optional collection name
            **kwargs: Additional retrieval options

        Returns:
            List of document data
        """
        if isinstance(document_ids, str):
            document_ids = [document_ids]

        results = self.collection.get(ids=document_ids)
        documents = []

        for i, doc_id in enumerate(results["ids"]):
            documents.append(
                {
                    "id": doc_id,
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
            )

        return documents

    async def list_documents(
        self,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List all documents in the collection.

        Args:
            collection_name: Optional collection name
            **kwargs: Additional listing options

        Returns:
            List of document data
        """
        results = self.collection.get()
        documents = []

        for i, doc_id in enumerate(results["ids"]):
            documents.append(
                {
                    "id": doc_id,
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
            )

        return documents

    async def clear(self, **kwargs: Any) -> None:
        """Clear all documents from the collection.

        Args:
            **kwargs: Additional clearing options
        """
        self.collection.delete()

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
            Number of documents in the collection
        """
        return self.collection.count()

    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary of collection statistics
        """
        return {
            "document_count": await self.count_documents(),
            "collection_name": self.collection_name,
            "has_persistence": self.path is not None,
        }
