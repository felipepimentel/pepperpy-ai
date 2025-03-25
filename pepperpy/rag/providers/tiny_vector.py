"""TinyVectorDB provider implementation for RAG capabilities.

This module provides a TinyVectorDB-based implementation of the RAG provider interface,
using TinyVectorDB for lightweight vector storage and retrieval with SQLite backend.

Example:
    >>> from pepperpy.rag import RAGProvider
    >>> provider = RAGProvider.from_config({
    ...     "provider": "tiny_vector",
    ...     "path": "./tiny_vector.db"
    ... })
    >>> await provider.add_documents([
    ...     Document(text="Example document", metadata={"source": "test"})
    ... ])
    >>> results = await provider.search("query", top_k=3)
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.utils import import_provider, lazy_provider_class
from pepperpy.rag.base import (
    BaseProvider,
    Document,
    Query,
    RetrievalResult,
)

logger = logging.getLogger(__name__)


@lazy_provider_class("rag", "tiny_vector")
class TinyVectorProvider(BaseProvider):
    """TinyVectorDB implementation of the RAG provider interface.

    This provider supports:
    - SQLite-based vector storage
    - JIT-optimized vector operations
    - Lightweight and easy to use
    - No numpy dependency
    """

    name = "tiny_vector"

    def __init__(
        self,
        path: Optional[str] = None,
        collection_name: str = "pepperpy",
        **kwargs: Any,
    ) -> None:
        """Initialize TinyVectorDB provider.

        Args:
            path: Path to SQLite database file
            collection_name: Name of the collection to use
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)

        self.path = path or "tiny_vector.db"
        self.collection_name = collection_name
        self.db = None
        self._collection = None

    async def initialize(self) -> None:
        """Initialize the provider.

        This method sets up the TinyVectorDB database and collection.
        """
        # Import tiny_vectordb only when provider is instantiated
        tiny_vectordb = import_provider("tiny_vectordb", "rag", "tiny_vector")

        # Initialize database
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.db = tiny_vectordb.Database(self.path)
        self._collection = self.db.get_or_create_collection(self.collection_name)

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            The provider configuration
        """
        return {
            "path": self.path,
            "collection_name": self.collection_name,
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
            "max_batch_size": 1000,
            "max_dimensions": 1536,
        }

    async def add_documents(
        self,
        documents: List[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the collection.

        Args:
            documents: List of documents to add
            **kwargs: Additional options
        """
        if not self._collection:
            await self.initialize()

        # Convert documents to TinyVectorDB format
        for doc in documents:
            doc_id = doc.get("id") or str(uuid.uuid4())
            self._collection.add(
                id=doc_id,
                vector=doc.get("embeddings", []),
                metadata={"text": doc["text"], **(doc.get("metadata", {}))},
            )

    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> List[RetrievalResult]:
        """Search for documents similar to query.

        Args:
            query: Query to search for
            limit: Maximum number of results to return
            **kwargs: Additional search options

        Returns:
            List of retrieval results
        """
        if not self._collection:
            await self.initialize()

        # Search collection
        results = self._collection.search(
            query_vector=query.embeddings, k=limit, **kwargs
        )

        # Convert results to RetrievalResult objects
        retrieval_results = []
        for result in results:
            doc = Document(
                text=result.metadata["text"],
                metadata={k: v for k, v in result.metadata.items() if k != "text"},
            )
            doc.update({
                "id": result.id,
                "embeddings": result.vector,
            })

            retrieval_results.append(
                RetrievalResult(
                    query=query,
                    documents=[doc],
                    scores=[float(result.score)] if hasattr(result, "score") else None,
                )
            )

        return retrieval_results

    async def delete_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Delete documents from collection.

        Args:
            document_ids: List of document IDs to delete
            **kwargs: Additional options
        """
        if not self._collection:
            await self.initialize()

        for doc_id in document_ids:
            self._collection.delete(doc_id)

    async def get_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID.

        Args:
            document_id: ID of document to get
            **kwargs: Additional options

        Returns:
            Document if found, None otherwise
        """
        if not self._collection:
            await self.initialize()

        try:
            result = self._collection.get(document_id)
            if not result:
                return None

            return {
                "id": result.id,
                "text": result.metadata["text"],
                "metadata": {k: v for k, v in result.metadata.items() if k != "text"},
                "embeddings": result.vector,
            }
        except Exception:
            return None

    async def get_documents(
        self,
        document_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Get multiple documents by ID.

        Args:
            document_ids: ID or list of IDs of documents to get
            **kwargs: Additional options

        Returns:
            List of found documents
        """
        if isinstance(document_ids, str):
            document_ids = [document_ids]

        documents = []
        for doc_id in document_ids:
            doc = await self.get_document(doc_id, **kwargs)
            if doc:
                documents.append(doc)

        return documents

    async def list_documents(
        self,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """List all documents in the collection.

        Args:
            **kwargs: Additional options

        Returns:
            List of all documents
        """
        if not self._collection:
            await self.initialize()

        results = self._collection.list()
        documents = []

        for result in results:
            documents.append({
                "id": result.id,
                "text": result.metadata["text"],
                "metadata": {k: v for k, v in result.metadata.items() if k != "text"},
                "embeddings": result.vector,
            })

        return documents

    async def clear(self, **kwargs: Any) -> None:
        """Clear all documents from the collection.

        Args:
            **kwargs: Additional options
        """
        if not self._collection:
            await self.initialize()

        self._collection.clear()

    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the entire collection.

        Args:
            **kwargs: Additional options
        """
        if not self._collection:
            await self.initialize()

        self.db.delete_collection(self.collection_name)
        self._collection = None

    async def count_documents(self, **kwargs: Any) -> int:
        """Get total number of documents in collection.

        Args:
            **kwargs: Additional options

        Returns:
            Number of documents
        """
        if not self._collection:
            await self.initialize()

        return len(self._collection)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.

        Returns:
            Dictionary containing statistics.
        """
        return {
            "count": await self.count_documents(),
            "name": self.collection_name,
            "path": self.path,
        }
