"""Interfaces for the RAG module.

This module defines the interfaces used throughout the RAG module,
providing a central location for all interface definitions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

from pepperpy.rag.document.core import Document

# Type variables for generic interfaces
T = TypeVar("T")
U = TypeVar("U")
Input = TypeVar("Input")
Output = TypeVar("Output")


# Document-related interfaces
class DocumentLoader(ABC):
    """Interface for document loaders.

    Document loaders are responsible for loading documents from various sources,
    such as files, databases, or APIs.
    """

    @abstractmethod
    def load(self, source: str, **kwargs: Any) -> List[Document]:
        """Load documents from a source.

        Args:
            source: The source to load documents from
            **kwargs: Additional arguments for loading

        Returns:
            List of loaded documents

        Raises:
            DocumentLoadError: If loading fails
        """
        pass


class DocumentProcessor(ABC):
    """Interface for document processors.

    Document processors transform documents in some way, such as by
    extracting text, cleaning content, or adding metadata.
    """

    @abstractmethod
    def process(self, document: Document, **kwargs: Any) -> Document:
        """Process a document.

        Args:
            document: The document to process
            **kwargs: Additional arguments for processing

        Returns:
            The processed document

        Raises:
            DocumentProcessError: If processing fails
        """
        pass


class DocumentStore(ABC):
    """Interface for document stores.

    Document stores are responsible for storing and retrieving documents.
    """

    @abstractmethod
    def add(self, documents: List[Document], **kwargs: Any) -> List[str]:
        """Add documents to the store.

        Args:
            documents: The documents to add
            **kwargs: Additional arguments for adding

        Returns:
            List of document IDs

        Raises:
            DocumentStoreError: If adding fails
        """
        pass

    @abstractmethod
    def get(self, document_id: str, **kwargs: Any) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: The ID of the document to get
            **kwargs: Additional arguments for getting

        Returns:
            The document, or None if not found

        Raises:
            DocumentStoreError: If getting fails
        """
        pass

    @abstractmethod
    def search(
        self, query_embedding: List[float], top_k: int = 5, **kwargs: Any
    ) -> tuple[List[Document], List[float]]:
        """Search for documents by embedding.

        Args:
            query_embedding: The query embedding to search with
            top_k: The number of results to return
            **kwargs: Additional arguments for searching

        Returns:
            Tuple of (documents, scores)

        Raises:
            DocumentStoreError: If searching fails
        """
        pass


# Vector store interface
class VectorStore(ABC):
    """Interface for vector stores.

    Vector stores are specialized document stores that support
    vector similarity search.
    """

    @abstractmethod
    def add_embeddings(
        self, embeddings: List[List[float]], documents: List[Document], **kwargs: Any
    ) -> List[str]:
        """Add embeddings and documents to the store.

        Args:
            embeddings: The embeddings to add
            documents: The documents to add
            **kwargs: Additional arguments for adding

        Returns:
            List of document IDs

        Raises:
            VectorStoreError: If adding fails
        """
        pass

    @abstractmethod
    def similarity_search(
        self, query_embedding: List[float], top_k: int = 5, **kwargs: Any
    ) -> tuple[List[Document], List[float]]:
        """Search for similar documents by embedding.

        Args:
            query_embedding: The query embedding to search with
            top_k: The number of results to return
            **kwargs: Additional arguments for searching

        Returns:
            Tuple of (documents, scores)

        Raises:
            VectorStoreError: If searching fails
        """
        pass


# Transformation interfaces
class DocumentTransformer(ABC):
    """Interface for document transformers.

    Document transformers apply transformations to documents,
    such as text extraction, HTML cleaning, or language detection.
    """

    @abstractmethod
    def transform(self, document: Document, **kwargs: Any) -> Document:
        """Transform a document.

        Args:
            document: The document to transform
            **kwargs: Additional arguments for transformation

        Returns:
            The transformed document

        Raises:
            TransformError: If transformation fails
        """
        pass


# Metadata interfaces
class MetadataExtractor(ABC):
    """Interface for metadata extractors.

    Metadata extractors extract metadata from documents,
    such as authors, creation dates, or keywords.
    """

    @abstractmethod
    def extract(self, document: Document, **kwargs: Any) -> Dict[str, Any]:
        """Extract metadata from a document.

        Args:
            document: The document to extract metadata from
            **kwargs: Additional arguments for extraction

        Returns:
            Dictionary of extracted metadata

        Raises:
            MetadataExtractionError: If extraction fails
        """
        pass


# Pipeline interfaces
class PipelineStage(ABC):
    """Interface for pipeline stages.

    Pipeline stages are components in a processing pipeline
    that transform inputs into outputs.
    """

    @abstractmethod
    def process(self, inputs: Any) -> Any:
        """Process the stage inputs.

        Args:
            inputs: The stage inputs

        Returns:
            The stage outputs

        Raises:
            PipelineError: If processing fails
        """
        pass


class AbstractPipelineStage(Generic[Input, Output], ABC):
    """Generic interface for pipeline stages.

    This interface provides a more strongly typed version of PipelineStage.
    """

    @abstractmethod
    async def process(
        self,
        input_data: Input,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Output:
        """Process input data.

        Args:
            input_data: The input data to process
            metadata: Optional metadata to include with the processing

        Returns:
            The processed output data

        Raises:
            PipelineError: If processing fails
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the stage configuration.

        Returns:
            True if the configuration is valid, False otherwise
        """
        pass


# Provider interfaces
class EmbeddingProvider(Protocol):
    """Interface for embedding providers.

    Embedding providers convert text into vector embeddings.
    """

    def embed_query(self, query: str) -> List[float]:
        """Embed a query.

        Args:
            query: The query to embed

        Returns:
            The query embedding
        """
        ...

    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        """Embed documents.

        Args:
            documents: The documents to embed

        Returns:
            The document embeddings
        """
        ...


class RerankerProvider(Protocol):
    """Interface for reranker providers.

    Reranker providers rerank documents based on relevance to a query.
    """

    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents based on a query.

        Args:
            query: The query for reranking
            documents: The documents to rerank

        Returns:
            The reranked documents
        """
        ...

    def get_scores(self, query: str, documents: List[Document]) -> List[float]:
        """Get reranking scores for documents.

        Args:
            query: The query for reranking
            documents: The documents to score

        Returns:
            The scores for each document
        """
        ...


class GenerationProvider(Protocol):
    """Interface for generation providers.

    Generation providers generate text based on a prompt.
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text based on a prompt.

        Args:
            prompt: The prompt for generation
            **kwargs: Additional arguments for generation

        Returns:
            The generated text
        """
        ...


class SearchProvider(Protocol):
    """Interface for search providers.

    Search providers search for documents based on a query.
    """

    def search(self, query: str, **kwargs: Any) -> List[Document]:
        """Search for documents based on a query.

        Args:
            query: The query to search for
            **kwargs: Additional arguments for searching

        Returns:
            List of matching documents
        """
        ...


# Reranking interfaces
class Reranker(ABC):
    """Interface for rerankers.

    Rerankers reorder documents based on relevance to a query.
    """

    @abstractmethod
    def rerank(
        self, query: str, documents: List[Document], **kwargs: Any
    ) -> List[Document]:
        """Rerank documents based on a query.

        Args:
            query: The query for reranking
            documents: The documents to rerank
            **kwargs: Additional arguments for reranking

        Returns:
            The reranked documents

        Raises:
            RerankingError: If reranking fails
        """
        pass
