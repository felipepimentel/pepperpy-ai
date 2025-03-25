"""ChromaDB vector store provider for RAG capabilities.

This module provides a ChromaDB-based implementation of the RAG provider interface,
supporting vector storage and retrieval for RAG operations.

Example:
    >>> from pepperpy.rag import RAGProvider
    >>> provider = RAGProvider.from_config({
    ...     "provider": "chroma",
    ...     "path": "./chroma_db"
    ... })
    >>> await provider.add_documents([
    ...     Document(text="Example document", metadata={"source": "test"})
    ... ])
    >>> results = await provider.search("query", top_k=3)
"""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Union

from pepperpy.core.base import ProviderError
from pepperpy.core.utils.imports import import_provider, lazy_provider_class
from pepperpy.rag.base import (
    BaseProvider,
    Document,
    Query,
    RetrievalResult,
)

logger = logging.getLogger(__name__)


@lazy_provider_class("rag", "chroma")
class ChromaProvider(BaseProvider):
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
            embedding_function: Optional custom embedding function
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
        """
        # Import chromadb only when provider is instantiated
        chromadb = import_provider("chromadb", "rag", "chroma")

        # Initialize client with persistence if path provided
        if self.path:
            os.makedirs(self.path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.path)
        else:
            self.client = chromadb.Client()

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
            texts.append(doc["text"])
            metadatas.append(doc.get("metadata", {}))
            if "embeddings" in doc:
                embeddings.append(doc["embeddings"])

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
    ) -> List[RetrievalResult]:
        """Search for documents similar to query.

        Args:
            query: Query to search for
            limit: Maximum number of results to return
            **kwargs: Additional search options

        Returns:
            List of retrieval results
        """
        # Convert query to ChromaDB format
        query_text = query.text

        # Search collection
        results = self.collection.query(
            query_texts=[query_text], n_results=limit, **kwargs
        )

        # Convert results to RetrievalResult objects
        retrieval_results = []
        for i in range(len(results["ids"][0])):
            doc = Document(
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
            )
            doc.update(
                {
                    "id": results["ids"][0][i],
                    "embeddings": results["embeddings"][0][i]
                    if results.get("embeddings")
                    else None,
                }
            )

            score = (
                float(results["distances"][0][i]) if "distances" in results else None
            )
            retrieval_results.append(
                RetrievalResult(
                    query=query,
                    documents=[doc],
                    scores=[score] if score is not None else None,
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
        self.collection.delete(ids=document_ids)

    async def get_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID.

        Args:
            document_id: ID of document to get
            collection_name: Optional name of the collection to get from
            **kwargs: Additional options

        Returns:
            Document if found, None otherwise
        """
        results = self.collection.get(ids=[document_id])
        if not results["ids"]:
            return None

        return {
            "id": results["ids"][0],
            "text": results["documents"][0],
            "metadata": results["metadatas"][0] if results["metadatas"] else {},
            "embeddings": results["embeddings"][0]
            if results.get("embeddings")
            else None,
        }

    async def get_documents(
        self,
        document_ids: Union[str, List[str]],
        collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Get multiple documents by ID.

        Args:
            document_ids: ID or list of IDs of documents to get
            collection_name: Optional name of the collection to get from
            **kwargs: Additional options

        Returns:
            List of found documents
        """
        if isinstance(document_ids, str):
            document_ids = [document_ids]

        results = self.collection.get(ids=document_ids)
        documents = []

        for i in range(len(results["ids"])):
            documents.append(
                {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    "embeddings": results["embeddings"][i]
                    if results.get("embeddings")
                    else None,
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
            collection_name: Optional name of the collection to list from
            **kwargs: Additional options

        Returns:
            List of all documents
        """
        results = self.collection.get()
        documents = []

        for i in range(len(results["ids"])):
            documents.append(
                {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                    "embeddings": results["embeddings"][i]
                    if results.get("embeddings")
                    else None,
                }
            )

        return documents

    async def clear(self, **kwargs: Any) -> None:
        """Clear all documents from the collection.

        Args:
            **kwargs: Additional options
        """
        if self._collection:
            self._collection.delete(where={})

    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the entire collection.

        Args:
            **kwargs: Additional options
        """
        if self.client and self._collection:
            self.client.delete_collection(self.collection_name)
            self._collection = None

    async def count_documents(self, **kwargs: Any) -> int:
        """Get total number of documents in collection.

        Args:
            **kwargs: Additional options

        Returns:
            Number of documents
        """
        return self.collection.count()

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
