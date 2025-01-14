"""Base RAG strategy module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TypedDict

from ....responses import AIResponse
from ..document import Document


class RAGSearchKwargs(TypedDict, total=False):
    """Search kwargs for RAG strategies."""

    limit: int | None
    threshold: float | None
    filter_criteria: dict[str, str] | None


class RAGGenerateKwargs(TypedDict, total=False):
    """Generate kwargs for RAG strategies."""

    temperature: float | None
    max_tokens: int | None
    model: str | None
    stream: bool


class BaseRAGStrategy(ABC):
    """Base class for RAG strategies."""

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        **kwargs: RAGSearchKwargs,
    ) -> list[Document]:
        """Search for documents.

        Args:
            query: Search query.
            limit: Maximum number of documents to return.
            **kwargs: Additional search parameters.

        Returns:
            list[Document]: List of relevant documents.
        """
        pass

    @abstractmethod
    async def generate(
        self,
        query: str,
        documents: list[Document],
        *,
        stream: bool = False,
        **kwargs: RAGGenerateKwargs,
    ) -> AIResponse | AsyncGenerator[AIResponse, None]:
        """Generate response from RAG.

        Args:
            query: User query.
            documents: Retrieved documents.
            stream: Whether to stream the response.
            **kwargs: Additional generation parameters.

        Returns:
            AIResponse | AsyncGenerator[AIResponse, None]: Generated response.
        """
        pass
