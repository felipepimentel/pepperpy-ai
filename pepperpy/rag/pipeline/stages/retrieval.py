"""Retrieval stage implementation.

This module provides functionality for retrieving relevant documents from a vector store.
"""

from typing import Any, Dict, List, Optional, Protocol, Union

from pepperpy.rag.errors import PipelineStageError
from pepperpy.rag.pipeline.base import BasePipelineStage
from pepperpy.rag.storage.base import BaseVectorStore
from pepperpy.rag.storage.types import Document, SearchResult


# Protocol for embedding providers
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    async def embed_query(self, text: str) -> List[float]:
        """Embed a query text.

        Args:
            text: The text to embed

        Returns:
            The embedding vector
        """
        ...


# Configuration for retrieval stage
class RetrievalStageConfig:
    """Configuration for retrieval stage."""

    def __init__(
        self,
        collection_name: str,
        limit: int = 10,
        min_score: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
    ):
        """Initialize retrieval stage configuration.

        Args:
            collection_name: Name of the collection to search.
            limit: Maximum number of documents to retrieve.
            min_score: Minimum score for documents to be included.
            filter: Filter to apply to the search.
        """
        self.collection_name = collection_name
        self.limit = limit
        self.min_score = min_score
        self.filter = filter


class RetrievalStage(BasePipelineStage):
    """Retrieval stage for finding relevant documents.

    This stage takes a query vector and retrieves relevant documents from a
    vector store based on similarity search.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        collection_name: str,
        limit: int = 10,
        min_score: Optional[float] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the retrieval stage.

        Args:
            vector_store: Vector store to retrieve documents from.
            collection_name: Name of the collection to search in.
            limit: Maximum number of documents to retrieve.
            min_score: Minimum similarity score for retrieved documents.
            filter: Metadata filter criteria.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.limit = limit
        self.min_score = min_score
        self.filter = filter

    async def process(
        self,
        query_vector: List[float],
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Process a query vector to retrieve relevant documents.

        Args:
            query_vector: Query vector to search with.
            **kwargs: Additional arguments passed to the vector store.

        Returns:
            List of search results sorted by relevance.

        Raises:
            PipelineStageError: If retrieval fails.
        """
        try:
            # Merge stage filter with any additional filter from kwargs
            filter = {**(self.filter or {}), **(kwargs.pop("filter", {}) or {})}

            # Search for similar documents
            results = await self.vector_store.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=kwargs.pop("limit", self.limit),
                min_score=kwargs.pop("min_score", self.min_score),
                filter=filter or None,
                **kwargs,
            )

            return results

        except Exception as e:
            raise PipelineStageError(f"Error retrieving documents: {str(e)}") from e

    async def add(
        self,
        documents: Union[Document, List[Document]],
        **kwargs: Any,
    ) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: Document or list of documents to add.
            **kwargs: Additional arguments passed to the vector store.

        Returns:
            List of document IDs.

        Raises:
            PipelineStageError: If adding documents fails.
        """
        try:
            return await self.vector_store.add(
                collection_name=self.collection_name,
                documents=documents,
                **kwargs,
            )

        except Exception as e:
            raise PipelineStageError(f"Error adding documents: {str(e)}") from e

    async def delete(
        self,
        doc_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> List[str]:
        """Delete documents from the vector store.

        Args:
            doc_ids: Document ID or list of document IDs to delete.
            **kwargs: Additional arguments passed to the vector store.

        Returns:
            List of successfully deleted document IDs.

        Raises:
            PipelineStageError: If deleting documents fails.
        """
        try:
            return await self.vector_store.delete(
                collection_name=self.collection_name,
                doc_ids=doc_ids,
                **kwargs,
            )

        except Exception as e:
            raise PipelineStageError(f"Error deleting documents: {str(e)}") from e

    async def clear(self, **kwargs: Any) -> None:
        """Clear all documents from the vector store collection.

        Args:
            **kwargs: Additional arguments passed to the vector store.

        Raises:
            PipelineStageError: If clearing documents fails.
        """
        try:
            await self.vector_store.delete_collection(
                collection_name=self.collection_name,
                **kwargs,
            )
            await self.vector_store.create_collection(
                collection_name=self.collection_name,
                **kwargs,
            )

        except Exception as e:
            raise PipelineStageError(f"Error clearing documents: {str(e)}") from e
