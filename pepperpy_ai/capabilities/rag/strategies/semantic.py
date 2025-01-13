"""Semantic RAG strategy module."""

from collections.abc import AsyncGenerator
from typing import Any, TypedDict, TypeVar, cast

from ....ai_types import Message, MessageRole
from ....providers.base import BaseProvider
from ....responses import AIResponse
from ..base import Document, RAGCapability, RAGConfig, RAGGenerateKwargs

T = TypeVar("T", bound=BaseProvider[Any])

class SemanticSearchKwargs(TypedDict, total=False):
    """Type hints for semantic search kwargs."""
    limit: int | None
    threshold: float
    filter_criteria: dict[str, str]

class SemanticRAGStrategy(RAGCapability[T]):
    """Semantic RAG strategy implementation."""

    def __init__(self, config: RAGConfig, provider: type[T]) -> None:
        """Initialize semantic RAG strategy.

        Args:
            config: Strategy configuration
            provider: Provider class to use
        """
        super().__init__(config, provider)
        self._documents: list[Document] = []

    async def _stream_generate(
        self,
        query: str,
        documents: list[Document],
        **kwargs: RAGGenerateKwargs,
    ) -> AsyncGenerator[AIResponse, None]:
        """Generate streaming responses.

        Args:
            query: User query.
            documents: Retrieved documents.
            **kwargs: Additional generation parameters.

        Returns:
            An async generator of responses.

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")

        # Extract kwargs for provider
        model = cast(str | None, kwargs.get("model"))
        temperature = cast(float | None, kwargs.get("temperature", 0.7))
        max_tokens = cast(int | None, kwargs.get("max_tokens"))

        # Prepare messages with context from documents
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful AI assistant."),
            Message(role=MessageRole.USER, content=query),
        ]

        async for response in self._provider_instance.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield response

    async def _generate_single(
        self,
        query: str,
        documents: list[Document],
        **kwargs: RAGGenerateKwargs,
    ) -> AIResponse:
        """Generate a single response.

        Args:
            query: User query.
            documents: Retrieved documents.
            **kwargs: Additional generation parameters.

        Returns:
            The generated response.

        Raises:
            RuntimeError: If provider is not initialized or no response received
        """
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")

        # Extract kwargs for provider
        model = cast(str | None, kwargs.get("model"))
        temperature = cast(float | None, kwargs.get("temperature", 0.7))
        max_tokens = cast(int | None, kwargs.get("max_tokens"))

        # Prepare messages with context from documents
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful AI assistant."),
            Message(role=MessageRole.USER, content=query),
        ]

        async for response in self._provider_instance.stream(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            return response
        raise RuntimeError("No response received from provider")

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
            Generated response or stream of responses.

        Raises:
            RuntimeError: If provider is not initialized.
        """
        if not self.is_initialized:
            await self.initialize()

        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")

        if stream:
            return self._stream_generate(query, documents, **kwargs)
        return await self._generate_single(query, documents, **kwargs)

    async def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
