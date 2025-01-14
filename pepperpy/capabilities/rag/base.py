"""Base RAG strategy module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, TypedDict

from ...responses import AIResponse
from ...types import Message
from ..base import BaseCapability
from ..chat.base import BaseChatCapability


class Document(TypedDict):
    """Document type."""

    content: str
    metadata: dict[str, str | int | float | bool | None]


class BaseRAGStrategy(ABC):
    """Base RAG strategy."""

    def __init__(self, chat_capability: BaseChatCapability) -> None:
        """Initialize RAG strategy.

        Args:
            chat_capability: Chat capability to use for responses
        """
        self.chat_capability = chat_capability

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the strategy.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional strategy-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        raise NotImplementedError

    @abstractmethod
    async def get_similar_documents(self, query: str) -> str:
        """Get similar documents for a query.

        Args:
            query: Query to find similar documents for

        Returns:
            Similar documents as a string
        """
        raise NotImplementedError


class RAGCapability(BaseCapability):
    """Base RAG capability."""

    def __init__(
        self, config: dict[str, Any], chat_capability: BaseChatCapability
    ) -> None:
        """Initialize RAG capability.

        Args:
            config: RAG configuration
            chat_capability: Chat capability to use for responses
        """
        super().__init__(config)
        self.chat_capability = chat_capability

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[AIResponse, None]:
        """Stream responses from the capability.

        Args:
            messages: List of messages to send
            model: Model to use for completion
            temperature: Temperature to use for completion
            max_tokens: Maximum number of tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            AsyncGenerator yielding AIResponse objects
        """
        raise NotImplementedError
