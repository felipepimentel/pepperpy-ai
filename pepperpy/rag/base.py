"""Base interfaces and components for RAG functionality."""

import importlib
from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

from pepperpy.core.errors import ValidationError
from pepperpy.plugins.plugin import PepperpyPlugin
from pepperpy.workflow.base import WorkflowComponent

T = TypeVar("T")


class RAGError(Exception):
    """Base exception class for RAG errors."""

    pass


class ProviderError(RAGError):
    """Raised when a provider operation fails."""

    pass


@dataclass
class Document:
    """Document for RAG."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    _data: dict[str, Any] = field(default_factory=dict)

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

    def update(self, data: dict[str, Any]) -> None:
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
    metadata: dict[str, Any] = field(default_factory=dict)
    embeddings: list[float] | None = None


@dataclass
class SearchResult:
    """Result from a search operation."""

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float | None = None

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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the result
        """
        return {
            "document": self.document,
            "score": self.score,
        }


class RAGProvider(PepperpyPlugin):
    """Base class for RAG providers."""

    @abstractmethod
    async def store(self, docs: Document | list[Document]) -> None:
        """Store documents in the RAG context.

        Args:
            docs: Document or list of documents to store.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str | Query,
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
    async def get(self, doc_id: str) -> Document | None:
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

    async def add_documents(self, documents: list[Document]) -> None:
        """Add documents to the context.

        Args:
            documents: List of documents to add.
        """
        await self.provider.store(documents)

    async def search(self, query: Query) -> list[Document]:
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
        config: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
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

    async def process(self, data: str | Query) -> list[Document]:
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
    provider_type: str,
    **config: Any,
) -> RAGProvider:
    """Create a RAG provider instance.

    Args:
        provider_type: Type of provider to create
        **config: Provider configuration

    Returns:
        Instantiated RAG provider

    Raises:
        ValueError: If provider type is invalid
    """
    # Handle built-in provider types
    if provider_type == "memory":
        # Import here to avoid circular imports
        from pepperpy.rag.memory_provider import MemoryProvider

        return MemoryProvider(**config)
    else:
        try:
            # Try to create from plugin registry
            from pepperpy.plugins.registry import create_provider_instance

            return create_provider_instance("rag", provider_type, **config)
        except (ImportError, ValueError):
            # Try dynamic import for custom providers
            try:
                module_name = f"pepperpy.rag.providers.{provider_type}"
                module = importlib.import_module(module_name)

                # Find the provider class (assumed to be the only RAGProvider subclass)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, RAGProvider)
                        and attr != RAGProvider
                    ):
                        return attr(**config)

                raise ValueError(f"No RAGProvider subclass found in {module_name}")
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Invalid RAG provider type: {provider_type}") from e


class Filter:
    """Filter class for RAG queries."""

    def __init__(self, field: str, value: Any, operator: str = "eq"):
        """Initialize a filter.

        Args:
            field: The field to filter on
            value: The value to filter for
            operator: The operator to use (eq, ne, gt, lt, gte, lte, in, contains)
        """
        self.field = field
        self.value = value
        self.operator = operator

    def __repr__(self) -> str:
        return f"Filter(field='{self.field}', value='{self.value}', operator='{self.operator}')"
