"""Semantic RAG strategy module."""

from collections.abc import AsyncGenerator
from typing import Any, List, Optional, Type

from ....ai_types import Message, MessageRole
from ....responses import AIResponse
from ....providers.base import BaseProvider
from ..base import RAGCapability, RAGConfig, Document


class SemanticRAGStrategy(RAGCapability):
    """Semantic RAG strategy implementation."""

    def __init__(self, config: RAGConfig, provider: Type[BaseProvider[Any]]) -> None:
        """Initialize semantic RAG strategy.

        Args:
            config: Strategy configuration
            provider: Provider class to use
        """
        super().__init__(config, provider)
        self._documents: List[Document] = []
        self._provider_instance: Optional[BaseProvider[Any]] = None

    async def initialize(self) -> None:
        """Initialize strategy."""
        if not self.is_initialized:
            if not self._provider_instance:
                self._provider_instance = self.provider(self.config, self.config.api_key)
                await self._provider_instance.initialize()
            self._initialized = True

    async def cleanup(self) -> None:
        """Cleanup strategy resources."""
        if self.is_initialized:
            if self._provider_instance:
                await self._provider_instance.cleanup()
                self._provider_instance = None
            self._documents.clear()
            self._initialized = False

    async def add_document(self, document: Document) -> None:
        """Add document to RAG.

        Args:
            document: Document to add
        """
        self._documents.append(document)

    async def remove_document(self, document_id: str) -> None:
        """Remove document from RAG.

        Args:
            document_id: ID of document to remove
        """
        self._documents = [doc for doc in self._documents if doc.id != document_id]

    async def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Search for documents.

        Args:
            query: Search query
            limit: Maximum number of documents to return
            **kwargs: Additional search parameters

        Returns:
            List of matching documents
        """
        # Simple implementation for now
        return self._documents[:limit] if limit else self._documents

    async def _generate_stream(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Generate streaming responses.

        Args:
            messages: The messages to send to the provider.
            **kwargs: Additional generation parameters.

        Returns:
            An async generator of responses.

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")

        async for response in self._provider_instance.stream(messages, **kwargs):
            yield response

    async def _generate_single(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> AIResponse:
        """Generate a single response.

        Args:
            messages: The messages to send to the provider.
            **kwargs: Additional generation parameters.

        Returns:
            The generated response.

        Raises:
            RuntimeError: If provider is not initialized or no response received
        """
        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")

        async for response in self._provider_instance.stream(messages, **kwargs):
            return response
        raise RuntimeError("No response received from provider")

    async def generate(
        self,
        query: str,
        *,
        stream: bool = False,
        **kwargs: Any,
    ) -> AIResponse | AsyncGenerator[AIResponse, None]:
        """Generate response from RAG.

        Args:
            query: Query to generate response for
            stream: Whether to stream the response
            **kwargs: Additional generation parameters

        Returns:
            Generated response or stream of responses

        Raises:
            RuntimeError: If provider is not initialized
        """
        if not self.is_initialized:
            await self.initialize()

        if not self._provider_instance:
            raise RuntimeError("Provider not initialized")

        # Prepare messages with context from documents
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful AI assistant."),
            Message(role=MessageRole.USER, content=query),
        ]

        if stream:
            return self._generate_stream(messages, **kwargs)
        return await self._generate_single(messages, **kwargs)

    async def clear(self) -> None:
        """Clear all documents."""
        self._documents.clear()
