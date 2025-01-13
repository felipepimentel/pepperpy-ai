"""Semantic RAG strategy implementation."""

from collections.abc import AsyncGenerator
from typing import TypedDict

from ....responses import AIResponse
from ....types import Message, MessageRole
from ..base import BaseRAGStrategy


class SemanticKwargs(TypedDict, total=False):
    """Semantic strategy keyword arguments."""

    model: str
    temperature: float
    max_tokens: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    timeout: float


class SemanticStrategy(BaseRAGStrategy):
    """Semantic RAG strategy implementation."""

    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: SemanticKwargs,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the strategy.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        # Get last user message
        last_message = messages[-1]
        if last_message.role != MessageRole.USER:
            raise ValueError("Last message must be from user")

        # Get similar documents
        similar_docs = await self.get_similar_documents(last_message.content)

        # Create context message
        context_message = Message(
            role=MessageRole.SYSTEM,
            content=f"Here are some relevant documents:\n{similar_docs}",
        )

        # Add context to messages
        messages_with_context = [context_message, *messages]

        # Stream responses from chat capability
        stream = self.chat_capability.stream(
            messages_with_context,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        async for response in stream:
            yield response

    async def get_similar_documents(self, query: str) -> str:
        """Get similar documents for a query.

        Args:
            query: Query to find similar documents for

        Returns:
            Similar documents as a string
        """
        # TODO: Implement document retrieval
        return "No documents found."
