"""Base RAG module."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...ai_types import Message
from ...responses import AIResponse
from ..base import BaseCapability, CapabilityConfig


@dataclass
class RAGConfig(CapabilityConfig):
    """RAG capability configuration."""

    name: str = "rag"
    version: str = "1.0.0"
    enabled: bool = True
    model_name: str = "default"
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32
    temperature: float = 0.7
    max_tokens: int = 1024
    api_key: str = ""
    similarity_threshold: float = 0.5
    max_documents: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Document for RAG."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGCapability(BaseCapability[RAGConfig], ABC):
    """Base class for RAG capabilities."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize RAG capability."""
        raise NotImplementedError

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup RAG capability resources."""
        raise NotImplementedError

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        """Add document to RAG.

        Args:
            document: Document to add
        """
        raise NotImplementedError

    @abstractmethod
    async def remove_document(self, document_id: str) -> None:
        """Remove document from RAG.

        Args:
            document_id: ID of document to remove
        """
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        """
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> None:
        """Clear all documents."""
        raise NotImplementedError
