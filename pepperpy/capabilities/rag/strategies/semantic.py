"""Semantic RAG strategy module."""

from collections.abc import AsyncGenerator
from typing import Any, TypedDict, cast

from ....responses import AIResponse
from ....types import Role
from ..document import Document
from .base import BaseRAGStrategy, RAGGenerateKwargs, RAGSearchKwargs


class SemanticKwargs(TypedDict, total=False):
    """Semantic kwargs for RAG strategies."""

    model: str | None
    temperature: float | None
    max_tokens: int | None


class SemanticRAGStrategy(BaseRAGStrategy):
    """Semantic RAG strategy."""

    def __init__(self, provider: Any) -> None:
        """Initialize semantic RAG strategy.

        Args:
            provider: Provider to use for embeddings and chat.
        """
        self.provider = provider
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Return whether the strategy is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the strategy."""
        if not self.is_initialized:
            await self.provider.initialize()
            self._initialized = True

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
        if not self.is_initialized:
            await self.initialize()

        return await self.get_relevant_documents(query)

    async def generate(
        self,
        query: str,
        documents: list[Document],
        *,
        stream: bool = False,
        **kwargs: RAGGenerateKwargs,
    ) -> AIResponse | AsyncGenerator[AIResponse, None]:
        """Generate a response.

        Args:
            query: User query.
            documents: List of relevant documents.
            stream: Whether to stream the response.
            **kwargs: Additional generation parameters.

        Returns:
            AIResponse | AsyncGenerator[AIResponse, None]: Generated response.
        """
        if not self.is_initialized:
            await self.initialize()

        # Create context message
        context = "\n\n".join(doc["content"] for doc in documents)
        system_message = {
            "role": Role.SYSTEM,
            "content": (
                "Here are some relevant documents that may help answer the question:\n"
                f"{context}"
            ),
        }

        # Create user message
        user_message = {
            "role": Role.USER,
            "content": query,
        }

        # Add context to messages
        messages = [system_message, user_message]

        # Stream responses from chat capability
        if stream:
            return cast(
                AsyncGenerator[AIResponse, None],
                self.provider.stream(
                    messages,
                    model=kwargs.get("model"),
                    temperature=kwargs.get("temperature"),
                    max_tokens=kwargs.get("max_tokens"),
                ),
            )
        else:
            return cast(
                AIResponse,
                await self.provider.chat(
                    messages,
                    model=kwargs.get("model"),
                    temperature=kwargs.get("temperature"),
                    max_tokens=kwargs.get("max_tokens"),
                ),
            )

    async def get_relevant_documents(self, query: str) -> list[Document]:
        """Get relevant documents for a query.

        Args:
            query: Query to get relevant documents for.

        Returns:
            list[Document]: List of relevant documents.
        """
        # TODO: Implement document retrieval
        return []
