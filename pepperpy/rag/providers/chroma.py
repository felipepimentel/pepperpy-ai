"""ChromaProvider implements RAG functionality using Chroma as the vector store.

This provider offers both in-memory and persistent storage options for vector embeddings,
making it ideal for development, testing, and production use cases.
"""

from typing import Any, Dict, List, Optional, Set, Union

import chromadb
from chromadb.config import Settings

from pepperpy.core import PepperpyError
from pepperpy.rag.base import BaseRAGProvider, Document, Query, RetrievalResult


class ChromaProvider(BaseRAGProvider):
    """Chroma-based RAG provider for vector storage and retrieval.
    
    This provider implements vector storage and similarity search using Chroma,
    a lightweight and efficient vector database that can run both in-memory
    and with persistent storage.

    Args:
        collection_name: Name of the collection to store vectors
        persist_directory: Optional path to store vectors persistently
    """

    def __init__(self, collection_name: str, persist_directory: Optional[str] = None):
        """Initialize the ChromaProvider.

        Args:
            collection_name: Name of the collection to store vectors
            persist_directory: Optional path to store vectors persistently
        """
        super().__init__()
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[Any] = None

    def _init_client(self) -> None:
        """Initialize the Chroma client if not already initialized."""
        if self._client is None:
            try:
                settings = Settings()
                if self.persist_directory:
                    self._client = chromadb.PersistentClient(
                        path=self.persist_directory, 
                        settings=settings
                    )
                else:
                    self._client = chromadb.EphemeralClient(settings=settings)
            except Exception as e:
                raise PepperpyError(f"Failed to initialize Chroma client: {str(e)}")

    async def initialize(self) -> None:
        """Initialize the provider and create/get the collection."""
        try:
            self._init_client()
            if self._client:
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name
                )
        except Exception as e:
            raise PepperpyError(f"Failed to initialize collection: {str(e)}")

    async def add_documents(
        self, documents: Union[Document, List[Document]]
    ) -> List[Document]:
        """Add documents to the provider.

        Args:
            documents: A document or list of documents to add.

        Returns:
            The added documents.

        Raises:
            PepperpyError: If there is an error adding the documents.
        """
        if not self._collection:
            await self.initialize()

        if isinstance(documents, Document):
            documents = [documents]

        try:
            # Extract components from the documents
            ids = [doc.id or str(i) for i, doc in enumerate(documents)]
            embeddings = [doc.embeddings for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            contents = [doc.content for doc in documents]

            # Add to collection
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=contents,
            )

            # Update document IDs
            for doc, doc_id in zip(documents, ids):
                doc.id = doc_id

            return documents
        except Exception as e:
            raise PepperpyError(f"Failed to add documents: {str(e)}")

    async def search(
        self,
        query: Query,
        limit: int = 10,
        min_score: Optional[float] = None,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents similar to the query.

        Args:
            query: The query to search for.
            limit: Maximum number of results to return.
            min_score: Minimum similarity score for results.
            **kwargs: Additional provider-specific arguments.

        Returns:
            A RetrievalResult containing the query and matching documents.

        Raises:
            PepperpyError: If there is an error performing the search.
        """
        if not self._collection:
            await self.initialize()

        try:
            # Perform the search
            results = self._collection.query(
                query_embeddings=[query.embeddings],
                n_results=limit,
                where=query.metadata,
            )

            # Convert to Documents
            documents = []
            scores = []
            for i in range(len(results["ids"][0])):
                doc = Document(
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    id=results["ids"][0][i],
                    embeddings=query.embeddings,  # Use query embeddings as approximation
                )
                documents.append(doc)
                scores.append(float(results["distances"][0][i]))

            # Filter by min_score if provided
            if min_score is not None:
                filtered = [
                    (doc, score)
                    for doc, score in zip(documents, scores)
                    if score >= min_score
                ]
                if filtered:
                    documents, scores = zip(*filtered)
                else:
                    documents, scores = [], []

            return RetrievalResult(
                query=query,
                documents=list(documents),
                scores=list(scores),
            )
        except Exception as e:
            raise PepperpyError(f"Failed to search documents: {str(e)}")

    async def delete_documents(self, document_ids: Union[str, List[str]]) -> None:
        """Delete documents from the provider.

        Args:
            document_ids: A document ID or list of document IDs to delete.

        Raises:
            PepperpyError: If there is an error deleting the documents.
        """
        if not self._collection:
            await self.initialize()

        if isinstance(document_ids, str):
            document_ids = [document_ids]

        try:
            self._collection.delete(ids=document_ids)
        except Exception as e:
            raise PepperpyError(f"Failed to delete documents: {str(e)}")

    async def get_documents(
        self, document_ids: Union[str, List[str]]
    ) -> List[Document]:
        """Get documents by their IDs.

        Args:
            document_ids: A document ID or list of document IDs to retrieve.

        Returns:
            The requested documents.

        Raises:
            PepperpyError: If there is an error retrieving the documents.
        """
        if not self._collection:
            await self.initialize()

        if isinstance(document_ids, str):
            document_ids = [document_ids]

        try:
            results = self._collection.get(ids=document_ids)
            documents = []
            for i in range(len(results["ids"])):
                doc = Document(
                    content=results["documents"][i],
                    metadata=results["metadatas"][i] if results["metadatas"] else {},
                    id=results["ids"][i],
                    embeddings=results["embeddings"][i] if results["embeddings"] else None,
                )
                documents.append(doc)
            return documents
        except Exception as e:
            raise PepperpyError(f"Failed to get documents: {str(e)}")

    async def list_documents(self) -> List[Document]:
        """List all documents in the provider.

        Returns:
            All documents in the provider.

        Raises:
            PepperpyError: If there is an error listing the documents.
        """
        if not self._collection:
            await self.initialize()

        try:
            results = self._collection.get()
            documents = []
            for i in range(len(results["ids"])):
                doc = Document(
                    content=results["documents"][i],
                    metadata=results["metadatas"][i] if results["metadatas"] else {},
                    id=results["ids"][i],
                    embeddings=results["embeddings"][i] if results["embeddings"] else None,
                )
                documents.append(doc)
            return documents
        except Exception as e:
            raise PepperpyError(f"Failed to list documents: {str(e)}")

    async def clear(self) -> None:
        """Clear all documents from the provider.

        Raises:
            PepperpyError: If there is an error clearing the documents.
        """
        if not self._collection:
            await self.initialize()

        try:
            self._collection.delete()
        except Exception as e:
            raise PepperpyError(f"Failed to clear documents: {str(e)}")

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            Dictionary with provider configuration.
        """
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
        }

    def get_capabilities(self) -> Dict[str, bool]:
        """Get the provider capabilities.

        Returns:
            Dictionary of supported capabilities.
        """
        return {
            "supports_metadata": True,
            "supports_async": True,
            "supports_batch_operations": True,
            "supports_persistence": bool(self.persist_directory),
        } 