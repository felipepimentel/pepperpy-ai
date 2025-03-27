"""Base RAG module."""

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Union

from pepperpy.core.base import (
    BaseProvider,
    ValidationError,
)
from pepperpy.core.workflow import WorkflowComponent
from pepperpy.rag.providers import RAGProvider
from pepperpy.rag.types import Document, Query

T = TypeVar("T")


@dataclass
class Document:
    """Document for RAG."""

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    _data: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Get item from document.

        Args:
            key: Key to get

        Returns:
            Value for key
        """
        if key == "text":
            return self.text
        if key == "metadata":
            return self.metadata
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item in document.

        Args:
            key: Key to set
            value: Value to set
        """
        if key == "text":
            self.text = value
        elif key == "metadata":
            self.metadata = value
        else:
            self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get item from document with default.

        Args:
            key: Key to get
            default: Default value if key not found

        Returns:
            Value for key or default
        """
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, data: Dict[str, Any]) -> None:
        """Update document with data.

        Args:
            data: Data to update with
        """
        for key, value in data.items():
            self[key] = value


@dataclass
class Query:
    """Query for RAG."""

    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class RetrievalResult:
    """Result from a RAG retrieval operation."""

    def __init__(self, document: Document, score: float = 0.0) -> None:
        """Initialize a retrieval result.

        Args:
            document: The retrieved document
            score: The relevance score (0.0 to 1.0)
        """
        self.document = document
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the result
        """
        return {
            "document": self.document,
            "score": self.score,
        }


class RAGProvider(BaseProvider):
    """Base class for RAG providers."""

    @abstractmethod
    async def store(self, documents: List[Document]) -> None:
        """Store documents in the RAG context.

        Args:
            documents: List of documents to store.
        """
        pass

    @abstractmethod
    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query.

        Returns:
            List of relevant documents.
        """
        pass


class RAGContext:
    """Context for RAG operations."""

    def __init__(self, provider: RAGProvider) -> None:
        """Initialize the RAG context.

        Args:
            provider: The RAG provider to use.
        """
        self.provider = provider

    async def initialize(self) -> None:
        """Initialize the context."""
        await self.provider.initialize()

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.provider.cleanup()

    async def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the context.

        Args:
            documents: List of documents to add.
        """
        await self.provider.store(documents)

    async def search(self, query: Query) -> List[Document]:
        """Search for relevant documents.

        Args:
            query: Search query.

        Returns:
            List of relevant documents.
        """
        return await self.provider.search(query)


class RAGComponent(WorkflowComponent):
    """Component for Retrieval Augmented Generation (RAG).

    This component handles the retrieval of relevant documents based on input queries.
    """

    def __init__(
        self,
        component_id: str,
        name: str,
        provider: RAGProvider,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RAG component.

        Args:
            component_id: Unique identifier for the component
            name: Human-readable name
            provider: RAG provider implementation
            config: Optional configuration
            metadata: Optional metadata
        """
        super().__init__(
            component_id=component_id,
            name=name,
            provider=provider,
            config=config,
            metadata=metadata,
        )

    async def process(self, data: Union[str, Query]) -> List[Document]:
        """Process input data and retrieve relevant documents.

        Args:
            data: Input query as string or Query object

        Returns:
            List of relevant documents

        Raises:
            ValidationError: If input type is invalid
        """
        if isinstance(data, str):
            query = Query(text=data)
        elif isinstance(data, Query):
            query = data
        else:
            raise ValidationError(
                f"Invalid input type for RAG component: {type(data).__name__}. "
                "Expected str or Query."
            )

        return await self.provider.search(query)

    async def cleanup(self) -> None:
        """Clean up component resources."""
        if self.provider:
            await self.provider.cleanup()
