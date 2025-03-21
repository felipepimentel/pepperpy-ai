"""Provider module for RAG functionality.

This module provides the base provider interface for RAG operations.
"""

import logging
from abc import abstractmethod
from typing import Any, List, Optional, Protocol, runtime_checkable

from .document import Document
from .query import Query
from .result import RetrievalResult

logger = logging.getLogger(__name__)


class RAGError(Exception):
    """Base class for RAG-related errors."""

    pass


@runtime_checkable
class RAGProvider(Protocol):
    """Protocol for RAG providers.

    This protocol defines the interface that all RAG providers must implement.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should perform any necessary setup, such as connecting
        to databases or loading models.

        Raises:
            RAGError: If initialization fails
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Shut down the provider.

        This method should clean up any resources used by the provider.

        Raises:
            RAGError: If shutdown fails
        """
        ...

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        **kwargs: Any,
    ) -> None:
        """Add documents to the provider.

        Args:
            documents: Documents to add
            **kwargs: Additional provider-specific arguments

        Raises:
            RAGError: If adding documents fails
        """
        ...

    @abstractmethod
    async def remove_documents(
        self,
        document_ids: List[str],
        **kwargs: Any,
    ) -> None:
        """Remove documents from the provider.

        Args:
            document_ids: IDs of documents to remove
            **kwargs: Additional provider-specific arguments

        Raises:
            RAGError: If removing documents fails
        """
        ...

    @abstractmethod
    async def search(
        self,
        query: Query,
        limit: int = 10,
        **kwargs: Any,
    ) -> RetrievalResult:
        """Search for documents matching a query.

        Args:
            query: Query to search for
            limit: Maximum number of results to return
            **kwargs: Additional provider-specific arguments

        Returns:
            Search results

        Raises:
            RAGError: If search fails
        """
        ...

    @abstractmethod
    async def get_document(
        self,
        document_id: str,
        **kwargs: Any,
    ) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: ID of document to get
            **kwargs: Additional provider-specific arguments

        Returns:
            Document if found, None otherwise

        Raises:
            RAGError: If getting document fails
        """
        ...

    @abstractmethod
    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Document]:
        """List documents in the provider.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            **kwargs: Additional provider-specific arguments

        Returns:
            List of documents

        Raises:
            RAGError: If listing documents fails
        """
        ...
