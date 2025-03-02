"""Base classes for vector database providers.

This module defines the base abstractions for vector database providers
that can be used for retrieval in the RAG system.
"""

from abc import ABC, abstractmethod
from typing import List

from pepperpy.rag.retrieval.base import Retriever
from pepperpy.rag.types import SearchQuery, SearchResult


class VectorDBRetriever(Retriever, ABC):
    """Base class for vector database retrievers.

    This class defines the interface that all vector database retrievers
    must implement to be compatible with the RAG system.
    """

    @abstractmethod
    async def retrieve(self, query: SearchQuery, **kwargs) -> List[SearchResult]:
        """Retrieve documents from the vector database based on the query.

        Args:
            query: The search query to retrieve documents for
            **kwargs: Additional retriever-specific parameters

        Returns:
            A list of search results
        """
        pass
