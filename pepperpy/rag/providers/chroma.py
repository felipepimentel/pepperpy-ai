"""ChromaProvider implements RAG functionality using Chroma as the vector store.

This provider offers both in-memory and persistent storage options for vector embeddings,
making it ideal for development, testing, and production use cases.
"""

from typing import Any, Dict, List, Optional, Set
import chromadb
from chromadb.config import Settings
from pepperpy.rag.providers.base import BaseRAGProvider, SearchResult
from pepperpy.core import ProviderError

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
                raise ProviderError(f"Failed to initialize Chroma client: {str(e)}") from e

    async def initialize(self) -> None:
        """Initialize the provider and create/get the collection."""
        try:
            self._init_client()
            if self._client:
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name
                )
        except Exception as e:
            raise ProviderError(f"Failed to initialize collection: {str(e)}") from e

    async def store(self, vectors: List[Dict[str, Any]], batch_size: int = 100) -> None:
        """Store vectors in the collection.

        Args:
            vectors: List of vectors to store, each with 'values' and optional 'metadata'
            batch_size: Number of vectors to process in each batch

        Raises:
            ProviderError: If storing vectors fails
        """
        if not self._collection:
            await self.initialize()

        if self._collection:
            try:
                # Process in batches
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    
                    # Extract components from the vectors
                    ids = [str(v.get("id", i)) for i, v in enumerate(batch)]
                    embeddings = [v["values"] for v in batch]
                    metadatas = [v.get("metadata", {}) for v in batch]
                    
                    # Add to collection
                    self._collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        metadatas=metadatas
                    )
            except Exception as e:
                raise ProviderError(f"Failed to store vectors: {str(e)}") from e

    async def search(
        self, 
        query_vector: List[float], 
        top_k: int = 5, 
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar vectors in the collection.

        Args:
            query_vector: Vector to search for
            top_k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of SearchResult objects ordered by similarity

        Raises:
            ProviderError: If search fails
        """
        if not self._collection:
            await self.initialize()

        if self._collection:
            try:
                # Perform the search
                results = self._collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k,
                    where=filter
                )

                # Convert to SearchResult objects
                search_results = []
                for i in range(len(results['ids'][0])):
                    search_results.append(
                        SearchResult(
                            id=results['ids'][0][i],
                            score=float(results['distances'][0][i]),
                            metadata=results['metadatas'][0][i] if results['metadatas'] else {}
                        )
                    )

                return search_results
            except Exception as e:
                raise ProviderError(f"Failed to search vectors: {str(e)}") from e
        return []

    def get_config(self) -> Dict[str, Any]:
        """Get the provider configuration.

        Returns:
            Dictionary with provider configuration
        """
        return {
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory
        }

    def get_capabilities(self) -> Dict[str, bool]:
        """Get the provider capabilities.

        Returns:
            Dictionary of supported capabilities
        """
        return {
            "supports_metadata": True,
            "supports_async": True,
            "supports_batch_operations": True,
            "supports_persistence": bool(self.persist_directory)
        }

    async def close(self) -> None:
        """Close the provider and cleanup resources."""
        if self._client:
            try:
                # No need to explicitly persist - ChromaDB handles this automatically
                # for PersistentClient
                self._client = None
                self._collection = None
            except Exception as e:
                raise ProviderError(f"Failed to close provider: {str(e)}") from e 