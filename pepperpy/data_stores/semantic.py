"""Semantic RAG strategy module."""

from collections.abc import Sequence
from typing import Any

from pepperpy.capabilities.rag.document import Document
from pepperpy.capabilities.rag.strategies.base import BaseRAGStrategy
from pepperpy.types import MessageRole


class SemanticRAGStrategy(BaseRAGStrategy):
    """Semantic RAG strategy."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize semantic RAG strategy.

        Args:
            **kwargs: Additional arguments.
        """
        super().__init__(**kwargs)

    def _get_system_prompt(self, documents: Sequence[Document]) -> str:
        """Get system prompt.

        Args:
            documents: List of documents.

        Returns:
            str: System prompt.
        """
        return (
            "You are a helpful assistant that answers questions based on the provided "
            "context. Use the context to provide accurate and relevant answers. "
            "If you don't know the answer or if the context doesn't contain relevant "
            "information, say so. Do not make up information."
        )

    def _get_user_prompt(self, query: str, documents: Sequence[Document]) -> str:
        """Get user prompt.

        Args:
            query: User query.
            documents: List of documents.

        Returns:
            str: User prompt.
        """
        context = "\n\n".join(doc.content for doc in documents)
        return f"Context:\n{context}\n\nQuestion: {query}"

    def _get_messages(
        self, query: str, documents: Sequence[Document]
    ) -> list[dict[str, str]]:
        """Get messages for RAG.

        Args:
            query: User query.
            documents: List of documents.

        Returns:
            list[dict[str, str]]: List of messages.
        """
        return [
            {
                "role": MessageRole.SYSTEM.value,
                "content": self._get_system_prompt(documents),
            },
            {
                "role": MessageRole.USER.value,
                "content": self._get_user_prompt(query, documents),
            },
        ]
