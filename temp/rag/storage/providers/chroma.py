"""Chroma vector store provider implementation.

This module provides functionality for storing and retrieving vectors using Chroma.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from chromadb import PersistentClient
from chromadb.api.models.Collection import Collection as ChromaCollection

from pepperpy.errors import VectorStoreError
from pepperpy.rag.storage.base import BaseVectorStore
from pepperpy.rag.storage.types import Collection, Document, SearchResult


class ChromaVectorStore(BaseVectorStore):
    """Chroma-based vector store implementation.

    This provider uses Chroma for storing and retrieving vectors, making it
    suitable for production applications with persistence and efficient similarity search.
    """

    def __init__(
        self,
        persist_directory: Union[str, Path] = "./chroma_db",
        client_settings: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Chroma vector store.

        Args:
            persist_directory: Directory to persist the database to.
            client_settings: Settings for the Chroma client.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.persist_directory = Path(persist_directory)
        self.client_settings = client_settings or {}

        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize client and collections
        self._client: Optional[PersistentClient] = None
        self._collections: Dict[str, ChromaCollection] = {}

        # Initialize the client
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Chroma client.

        Raises:
            VectorStoreError: If client initialization fails.
        """
        try:
            self._client = PersistentClient(
                path=str(self.persist_directory),
                **self.client_settings,
            )
        except Exception as e:
            raise VectorStoreError(f"Error initializing Chroma client: {str(e)}") from e

    def _get_collection(self, collection_name: str) -> Optional[ChromaCollection]:
        """Get a Chroma collection by name.

        Args:
            collection_name: Name of the collection.

        Returns:
            The Chroma collection if it exists, None otherwise.

        Raises:
            VectorStoreError: If client is not initialized.
        """
        if not self._client:
            raise VectorStoreError("Chroma client is not initialized")

        try:
            if collection_name in self._collections:
                return self._collections[collection_name]

            # Check if collection exists
            for collection_info in self._client.list_collections():
                if collection_info.name == collection_name:
                    collection = self._client.get_collection(collection_name)
                    self._collections[collection_name] = collection
                    return collection

            return None

        except Exception as e:
            raise VectorStoreError(f"Error getting collection: {str(e)}") from e

    def _get_or_create_collection(self, collection_name: str) -> ChromaCollection:
        """Get or create a Chroma collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            The Chroma collection.

        Raises:
            VectorStoreError: If client is not initialized or operation fails.
        """
        if not self._client:
            raise VectorStoreError("Chroma client is not initialized")

        try:
            # Try to get existing collection
            collection = self._get_collection(collection_name)
            if collection:
                return collection

            # Create new collection
            collection = self._client.create_collection(name=collection_name)
            self._collections[collection_name] = collection
            return collection

        except Exception as e:
            raise VectorStoreError(f"Error creating collection: {str(e)}") from e

    async def add(
        self,
        collection_name: str,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> List[str]:
        """Add documents to a collection.

        Args:
            collection_name: Name of the collection.
            documents: Document or list of documents to add.
            **kwargs: Additional arguments.

        Returns:
            List of document IDs.

        Raises:
            VectorStoreError: If collection doesn't exist or documents are invalid.
        """
        try:
            # Convert single document to list
            if isinstance(documents, Document):
                documents = [documents]

            # Get or create collection
            collection = self._get_or_create_collection(collection_name)

            # Prepare data for Chroma
            ids = []
            embeddings = []
            metadatas = []
            contents = []

            for doc in documents:
                # Skip documents without vectors
                if not doc.vector:
                    continue

                # Add document data
                ids.append(str(doc.id))
                embeddings.append(doc.vector)
                metadatas.append(doc.metadata or {})
                contents.append("\n".join(chunk.content for chunk in doc.chunks))

            # Add to collection if we have valid documents
            if ids:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=contents,
                )

            return ids

        except Exception as e:
            raise VectorStoreError(f"Error adding documents: {str(e)}") from e

    async def get(
        self,
        collection_name: str,
        doc_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> Union[Optional[Document], List[Optional[Document]]]:
        """Get documents by ID.

        Args:
            collection_name: Name of the collection.
            doc_ids: Document ID or list of document IDs.
            **kwargs: Additional arguments.

        Returns:
            Document or list of documents (None for non-existent IDs).

        Raises:
            VectorStoreError: If collection doesn't exist.
        """
        try:
            # Get collection
            collection = self._get_collection(collection_name)
            if not collection:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Convert single ID to list
            single_id = isinstance(doc_ids, str)
            if single_id:
                doc_ids = [doc_ids]

            # Get documents from Chroma
            result = collection.get(
                ids=doc_ids,
                include=["embeddings", "metadatas", "documents"],
            )

            # Convert to Documents
            docs = []
            for i, doc_id in enumerate(result["ids"]):
                # Create document chunks from content
                content = result["documents"][i]
                chunks = [Document.Chunk(content=content)]

                # Create document
                doc = Document(
                    id=doc_id,
                    chunks=chunks,
                    vector=result["embeddings"][i],
                    metadata=result["metadatas"][i],
                )
                docs.append(doc)

            return docs[0] if single_id else docs

        except Exception as e:
            raise VectorStoreError(f"Error getting documents: {str(e)}") from e

    async def delete(
        self,
        collection_name: str,
        doc_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[str]:
        """Delete documents by ID.

        Args:
            collection_name: Name of the collection.
            doc_ids: Document ID or list of document IDs.
            **kwargs: Additional arguments.

        Returns:
            List of successfully deleted document IDs.

        Raises:
            VectorStoreError: If collection doesn't exist.
        """
        try:
            # Get collection
            collection = self._get_collection(collection_name)
            if not collection:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Convert single ID to list
            if isinstance(doc_ids, str):
                doc_ids = [doc_ids]

            # Delete documents
            collection.delete(ids=doc_ids)

            return doc_ids

        except Exception as e:
            raise VectorStoreError(f"Error deleting documents: {str(e)}") from e

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        min_score: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search for similar documents.

        Args:
            collection_name: Name of the collection.
            query_vector: Query vector.
            limit: Maximum number of results.
            min_score: Minimum similarity score.
            filter: Metadata filter criteria.
            **kwargs: Additional arguments.

        Returns:
            List of search results sorted by similarity.

        Raises:
            VectorStoreError: If collection doesn't exist or search fails.
        """
        try:
            # Get collection
            collection = self._get_collection(collection_name)
            if not collection:
                raise VectorStoreError(f"Collection {collection_name} does not exist")

            # Search in collection
            result = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=filter,
                include=["embeddings", "metadatas", "documents", "distances"],
            )

            # Convert to search results
            search_results = []
            for i in range(len(result["ids"][0])):
                # Create document chunks
                content = result["documents"][0][i]
                chunks = [Document.Chunk(content=content)]

                # Create document
                doc = Document(
                    id=result["ids"][0][i],
                    chunks=chunks,
                    vector=result["embeddings"][0][i],
                    metadata=result["metadatas"][0][i],
                )

                # Convert distance to similarity score (1 - distance)
                score = 1.0 - result["distances"][0][i]

                # Skip if below minimum score
                if min_score is not None and score < min_score:
                    continue

                # Create search result
                search_result = SearchResult(document=doc, score=score)
                search_results.append(search_result)

            return search_results

        except Exception as e:
            raise VectorStoreError(f"Error searching documents: {str(e)}") from e

    async def list_collections(self, **kwargs: Any) -> List[Collection]:
        """List all collections.

        Args:
            **kwargs: Additional arguments.

        Returns:
            List of collections.

        Raises:
            VectorStoreError: If operation fails.
        """
        try:
            if not self._client:
                raise VectorStoreError("Chroma client is not initialized")

            collections = []
            for collection_info in self._client.list_collections():
                collection = Collection(name=collection_info.name)
                collections.append(collection)

            return collections

        except Exception as e:
            raise VectorStoreError(f"Error listing collections: {str(e)}") from e

    async def get_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> Optional[Collection]:
        """Get a collection by name.

        Args:
            collection_name: Name of the collection.
            **kwargs: Additional arguments.

        Returns:
            Collection if it exists, None otherwise.

        Raises:
            VectorStoreError: If operation fails.
        """
        try:
            chroma_collection = self._get_collection(collection_name)
            if chroma_collection:
                return Collection(name=collection_name)
            return None

        except Exception as e:
            raise VectorStoreError(f"Error getting collection: {str(e)}") from e

    async def create_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> Collection:
        """Create a new collection.

        Args:
            collection_name: Name of the collection.
            **kwargs: Additional arguments.

        Returns:
            Created collection.

        Raises:
            VectorStoreError: If collection already exists or creation fails.
        """
        try:
            # Check if collection already exists
            if self._get_collection(collection_name):
                raise VectorStoreError(f"Collection {collection_name} already exists")

            # Create collection
            self._get_or_create_collection(collection_name)
            return Collection(name=collection_name)

        except Exception as e:
            raise VectorStoreError(f"Error creating collection: {str(e)}") from e

    async def delete_collection(
        self,
        collection_name: str,
        **kwargs: Any,
    ) -> bool:
        """Delete a collection.

        Args:
            collection_name: Name of the collection.
            **kwargs: Additional arguments.

        Returns:
            True if collection was deleted, False if it didn't exist.

        Raises:
            VectorStoreError: If operation fails.
        """
        try:
            if not self._client:
                raise VectorStoreError("Chroma client is not initialized")

            # Check if collection exists
            if not self._get_collection(collection_name):
                return False

            # Delete collection
            self._client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]

            return True

        except Exception as e:
            raise VectorStoreError(f"Error deleting collection: {str(e)}") from e

    async def clear(self, **kwargs: Any) -> None:
        """Clear all collections and data.

        Args:
            **kwargs: Additional arguments.

        Raises:
            VectorStoreError: If operation fails.
        """
        try:
            if not self._client:
                raise VectorStoreError("Chroma client is not initialized")

            # Get all collection names
            collection_names = [
                collection_info.name
                for collection_info in self._client.list_collections()
            ]

            # Delete all collections
            for collection_name in collection_names:
                self._client.delete_collection(collection_name)

            # Clear local cache
            self._collections.clear()

        except Exception as e:
            raise VectorStoreError(f"Error clearing vector store: {str(e)}") from e
