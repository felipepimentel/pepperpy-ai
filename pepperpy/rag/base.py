"""Base interfaces and components for RAG functionality."""

import importlib
import os
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, TypeVar, Union

from pepperpy.core.base import (
    BaseProvider,
    ValidationError,
)
from pepperpy.workflow.base import WorkflowComponent

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
    embeddings: Optional[List[float]] = None


@dataclass
class SearchResult:
    """Result from a search operation."""

    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: Optional[float] = None

    def to_document(self) -> Document:
        """Convert search result to document.

        Returns:
            Document representation
        """
        return Document(text=self.text, metadata=self.metadata)


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
    async def store(self, docs: Union[Document, List[Document]]) -> None:
        """Store documents in the RAG context.

        Args:
            docs: Document or list of documents to store.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: Union[str, Query],
        limit: int = 5,
        **kwargs: Any,
    ) -> Sequence[SearchResult]:
        """Search for relevant documents.

        Args:
            query: Search query text or Query object
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def get(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            doc_id: ID of the document to get

        Returns:
            The document if found, None otherwise
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
        results = await self.provider.search(query)
        return [result.to_document() for result in results]


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
            component_id=component_id, name=name, config=config, metadata=metadata
        )
        self.provider: RAGProvider = provider

    async def process(self, data: Union[str, Query]) -> List[Document]:
        """Process input data and generate a response.

        Args:
            data: Input text or query

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

        results = await self.provider.search(query)
        return [result.to_document() for result in results]

    async def cleanup(self) -> None:
        """Clean up component resources."""
        if self.provider:
            await self.provider.cleanup()


def create_provider(
    provider_type: str = "chroma",
    collection_name: str = "default",
    persist_directory: str = ".pepperpy/rag",
    **config: Any,
) -> RAGProvider:
    """Create a RAG provider based on type.

    Args:
        provider_type: Type of provider to create (default: chroma)
        collection_name: Name of the collection to use
        persist_directory: Directory to persist data
        **config: Provider configuration

    Returns:
        An instance of the specified RAGProvider

    Raises:
        ValidationError: If provider creation fails
    """
    try:
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)

        # Import provider module
        module_name = f"pepperpy.rag.providers.{provider_type}"
        module = importlib.import_module(module_name)

        # Get provider class
        provider_class_name = f"{provider_type.title()}Provider"
        provider_class = getattr(module, provider_class_name)

        # Create provider instance
        return provider_class(
            collection_name=collection_name,
            persist_directory=persist_directory,
            **config,
        )
    except (ImportError, AttributeError) as e:
        raise ValidationError(f"Failed to create RAG provider '{provider_type}': {e}")
