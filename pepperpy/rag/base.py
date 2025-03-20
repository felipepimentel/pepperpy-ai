"""Internal implementation of RAG provider functionality.

This module contains the implementation details of the RAG domain,
including data classes, provider base classes, and provider registry.
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Dict, List, Optional, Protocol, Type, Union

from pepperpy.common.providers import RestProvider
from pepperpy.core.errors import NotFoundError, PepperPyError

logger = logging.getLogger(__name__)

# Document Types


@dataclass
class Document:
    """A document for retrieval and context augmentation.

    Args:
        content: The document content
        metadata: Optional document metadata
            - source: Document source (e.g. "file", "database")
            - id: Unique document identifier
            - timestamp: Creation/update timestamp
            - custom: Additional metadata fields

    Example:
        >>> doc = Document(
        ...     content="The weather is sunny with a high of 75°F",
        ...     metadata={
        ...         "source": "weather_api",
        ...         "location": "San Francisco",
        ...         "timestamp": "2024-03-20T10:00:00Z"
        ...     }
        ... )
    """

    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Query:
    """A query for retrieving relevant documents.

    Args:
        text: The query text
        filters: Optional metadata filters to apply
        k: Number of documents to retrieve (default: 3)
        score_threshold: Minimum relevance score (0-1)
        metadata: Optional query metadata

    Example:
        >>> query = Query(
        ...     text="What is the weather in San Francisco?",
        ...     filters={"source": "weather_api"},
        ...     k=3,
        ...     score_threshold=0.7
        ... )
    """

    text: str
    filters: Optional[Dict[str, Any]] = None
    k: int = 3
    score_threshold: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RetrievalResult:
    """Result of a document retrieval operation.

    Args:
        documents: Retrieved documents
        scores: Relevance scores (0-1) for each document
        metadata: Optional result metadata
            - total_docs: Total documents in the collection
            - query_time: Time taken for retrieval in seconds
            - custom: Additional metadata fields

    Example:
        >>> result = RetrievalResult(
        ...     documents=[doc1, doc2],
        ...     scores=[0.95, 0.85],
        ...     metadata={"total_docs": 1000}
        ... )
    """

    documents: List[Document]
    scores: List[float]
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


# Provider Base Classes


class BaseProvider(Protocol):
    """Protocol for provider classes."""

    name: str

    def initialize(self) -> None:
        """Initialize the provider."""
        ...


# RAG Provider


class RAGProvider(RestProvider):
    """Base class for RAG (Retrieval Augmented Generation) providers."""

    def __init__(
        self,
        base_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize RAG provider.

        Args:
            base_url: Base URL for the REST API
            config: Optional configuration dictionary
        """
        super().__init__(base_url=base_url, config=config)

    @abstractmethod
    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        """Index documents for retrieval.

        Args:
            documents: List of documents to index. Each document should be a dictionary
                containing at least 'text' and 'metadata' fields.
            **kwargs: Additional parameters to pass to the provider
        """
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return
            **kwargs: Additional parameters to pass to the provider

        Returns:
            List of relevant documents with their metadata and scores
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_documents(
        self,
        document_ids: Union[str, List[str]],
        **kwargs: Any,
    ) -> None:
        """Delete documents from the index.

        Args:
            document_ids: Single document ID or list of document IDs to delete
            **kwargs: Additional parameters to pass to the provider
        """
        raise NotImplementedError

    @abstractmethod
    async def update_documents(
        self,
        documents: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        """Update existing documents in the index.

        Args:
            documents: List of documents to update. Each document should be a dictionary
                containing at least 'id', 'text', and 'metadata' fields.
            **kwargs: Additional parameters to pass to the provider
        """
        raise NotImplementedError

    def get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of this provider.

        Returns:
            A dictionary containing:
                - supported_models: List of supported embedding models
                - max_docs: Maximum documents per request
                - supports_filters: Whether metadata filtering is supported
                - additional provider-specific capabilities
        """
        return {"supported_models": [], "max_docs": 0, "supports_filters": False}


# Exceptions


class RAGError(PepperPyError):
    """Base exception for RAG-related errors."""

    pass


# Provider Registry

_PROVIDER_MODULES = {
    "openai": "..internal.providers.openai",
    "local": "..internal.providers.local",
    "chroma": "..internal.providers.chroma",
    "pinecone": "..internal.providers.pinecone",
}

_providers: Dict[str, Type[RAGProvider]] = {}


def _import_provider(name: str) -> Type[RAGProvider]:
    """Import a provider module and return its provider class."""
    if name not in _PROVIDER_MODULES:
        raise NotFoundError(f"Provider not found: {name}")

    try:
        module = import_module(_PROVIDER_MODULES[name], package=__package__)
        for attr in dir(module):
            obj = getattr(module, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, RAGProvider)
                and obj is not RAGProvider
                and getattr(obj, "name", None) == name
            ):
                return obj
        raise NotFoundError(f"Provider class not found in module: {name}")
    except ImportError as e:
        raise NotFoundError(f"Failed to import provider {name}: {e}")


def register_provider(name: str, provider_class: Type[RAGProvider]) -> None:
    """Register a provider class.

    Args:
        name: Provider name
        provider_class: Provider class to register
    """
    _providers[name] = provider_class


def get_provider(name: str) -> Type[RAGProvider]:
    """Get a registered provider class.

    Args:
        name: Provider name to get

    Returns:
        The provider class

    Raises:
        NotFoundError: If provider is not found
    """
    if name not in _providers:
        # Try to import provider
        provider_class = _import_provider(name)
        register_provider(name, provider_class)
    return _providers[name]


def list_providers() -> List[str]:
    """List all available provider names."""
    return list(_PROVIDER_MODULES.keys())
