"""Base RAG module."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Generic, TypedDict, TypeVar

from ...config.rag import RAGConfig
from ...providers.base import BaseProvider
from ...responses import AIResponse
from ..base import BaseCapability

T = TypeVar("T", bound=BaseProvider[Any])

@dataclass
class Document:
    """Document for RAG."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class RAGSearchKwargs(TypedDict, total=False):
    """Type hints for RAG search kwargs."""
    limit: int | None
    threshold: float
    filter_criteria: dict[str, str]


class RAGGenerateKwargs(TypedDict, total=False):
    """Type hints for RAG generate kwargs."""
    temperature: float
    max_tokens: int
    model: str
    stream: bool


class RAGCapability(BaseCapability[T], Generic[T]):
    """Base class for RAG capabilities."""

    def __init__(self, config: RAGConfig, provider: type[T]) -> None:
        """Initialize RAG capability.

        Args:
            config: RAG configuration.
            provider: Provider class to use.
        """
        super().__init__(config, provider)
        self._provider_instance: T | None = None

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
        **kwargs: RAGSearchKwargs,
    ) -> list[Document]:
        """Search for documents.

        Args:
            query: Query to search for.
            limit: Maximum number of documents to return.
            **kwargs: Additional search parameters.

        Returns:
            list[Document]: List of matching documents.
        """
        raise NotImplementedError

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
            stream: Whether to stream responses.
            **kwargs: Additional generation parameters.

        Returns:
            AIResponse | AsyncGenerator[AIResponse, None]: Generated response or stream.
        """
        raise NotImplementedError
