"""Base RAG module."""

import importlib
from abc import abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, TypeVar

from pepperpy.core.base import (
    BaseProvider,
    Component,
    ComponentError,
)

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


class RAGComponent(Component):
    """RAG workflow component.

    This component provides RAG capabilities to workflows by wrapping
    a RAGProvider instance.
    """

    def __init__(
        self,
        name: str = "rag",
        provider: Optional[RAGProvider] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize RAG component.

        Args:
            name: Component name
            provider: Optional RAGProvider instance
            config: Optional configuration dictionary
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self.provider = provider
        self.config = config or {}
        self.config.update(kwargs)

    async def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process inputs using the RAG provider.

        Args:
            inputs: Input data containing documents to store or query to search

        Returns:
            Output data containing search results or storage confirmation

        Raises:
            ComponentError: If processing fails
        """
        if not self.provider:
            provider_name = self.config.get("provider", "default")
            try:
                # Import the provider dynamically
                module_name = f"pepperpy.rag.providers.{provider_name}"
                try:
                    provider_module = importlib.import_module(module_name)
                    provider_class = getattr(
                        provider_module, f"{provider_name.title()}Provider"
                    )
                    self.provider = provider_class(
                        name=provider_name, config=self.config
                    )
                except (ImportError, AttributeError) as e:
                    raise ComponentError(f"Provider {provider_name} not found: {e}")
            except Exception as e:
                raise ComponentError(f"Failed to create RAG provider: {e}")

            try:
                await self.provider.initialize()
            except Exception as e:
                raise ComponentError(f"Failed to initialize RAG provider: {e}")

        try:
            if "documents" in inputs:
                # Store documents
                documents = [Document(**doc) for doc in inputs["documents"]]
                await self.provider.store(documents)
                return {"status": "stored"}
            elif "query" in inputs:
                # Search documents
                query = Query(**inputs["query"])
                results = await self.provider.search(query)
                return {"results": [asdict(doc) for doc in results]}
            else:
                raise ComponentError("No documents or query provided")
        except Exception as e:
            raise ComponentError(f"RAG processing failed: {e}")

    async def cleanup(self) -> None:
        """Clean up component resources."""
        if self.provider:
            await self.provider.cleanup()
