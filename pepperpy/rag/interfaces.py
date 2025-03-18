"""Interfaces for the RAG module.

This module defines the interfaces used throughout the RAG module,
providing a central location for all interface definitions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from pepperpy.rag.models import Document, DocumentChunk, ScoredChunk, VectorEmbedding

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
    async def load(self, source: str, **kwargs: Any) -> Document:
        """Load a document from a source.

        Args:
            source: The source to load the document from
            **kwargs: Additional arguments for loading

        Returns:
            The loaded document

        Raises:
            DocumentLoadError: If loading fails
        """
        pass


class DocumentProcessor(ABC):
    """Interface for document processors.

    Document processors are responsible for processing documents, such as
    splitting them into chunks, extracting metadata, or transforming the content.
    """

    @abstractmethod
    async def process(self, document: Document) -> List[DocumentChunk]:
        """Process a document.

        Args:
            document: The document to process

        Returns:
            The processed document chunks

        Raises:
            DocumentProcessError: If processing fails
        """
        pass


class DocumentStore(ABC):
    """Interface for document stores.

    Document stores are responsible for storing and retrieving documents.
    """

    @abstractmethod
    async def add_document(self, document: Document) -> None:
        """Add a document to the store.

        Args:
            document: The document to add

        Raises:
            StorageError: If adding fails
        """
        pass

    @abstractmethod
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the store.

        Args:
            chunks: The document chunks to add

        Raises:
            StorageError: If adding fails
        """
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: The ID of the document to get

        Returns:
            The document, or None if not found

        Raises:
            StorageError: If getting fails
        """
        pass

    @abstractmethod
    async def get_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get document chunks by document ID.

        Args:
            document_id: The ID of the document to get chunks for

        Returns:
            The document chunks

        Raises:
            StorageError: If getting fails
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """Delete a document from the store.

        Args:
            document_id: The ID of the document to delete

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def delete_chunks(self, document_id: str) -> None:
        """Delete document chunks from the store.

        Args:
            document_id: The ID of the document to delete chunks for

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_documents(self) -> List[Document]:
        """List all documents in the store.

        Returns:
            List of all documents

        Raises:
            StorageError: If listing fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the store.

        Raises:
            StorageError: If clearing fails
        """
        pass


# Vector store interface
class VectorStore(ABC):
    """Interface for vector stores.

    Vector stores are specialized document stores that support
    vector similarity search.
    """

    @abstractmethod
    async def add_embedding(self, embedding: VectorEmbedding) -> None:
        """Add an embedding to the store.

        Args:
            embedding: The embedding to add

        Raises:
            StorageError: If adding fails
        """
        pass

    @abstractmethod
    async def add_embeddings(self, embeddings: List[VectorEmbedding]) -> None:
        """Add embeddings to the store.

        Args:
            embeddings: The embeddings to add

        Raises:
            StorageError: If adding fails
        """
        pass

    @abstractmethod
    async def get_embedding(self, chunk_id: str) -> Optional[VectorEmbedding]:
        """Get an embedding by chunk ID.

        Args:
            chunk_id: The ID of the chunk to get the embedding for

        Returns:
            The embedding, or None if not found

        Raises:
            StorageError: If getting fails
        """
        pass

    @abstractmethod
    async def delete_embedding(self, chunk_id: str) -> None:
        """Delete an embedding from the store.

        Args:
            chunk_id: The ID of the chunk to delete the embedding for

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def delete_embeddings(self, document_id: str) -> None:
        """Delete embeddings from the store.

        Args:
            document_id: The ID of the document to delete embeddings for

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorEmbedding, float]]:
        """Search for similar embeddings.

        Args:
            query_vector: The query vector to search with
            limit: The maximum number of results to return
            min_score: The minimum similarity score to include
            filter_metadata: Optional metadata filters to apply

        Returns:
            List of (embedding, score) tuples, ordered by similarity

        Raises:
            StorageError: If searching fails
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear the store.

        Raises:
            StorageError: If clearing fails
        """
        pass


# Provider interfaces
class SearchProvider(ABC):
    """Interface for search providers.

    Search providers are responsible for searching for documents
    based on a query.
    """

    @abstractmethod
    async def search(self, query: str, **kwargs: Any) -> List[Document]:
        """Search for documents.

        Args:
            query: The search query
            **kwargs: Additional arguments for searching

        Returns:
            List of matching documents

        Raises:
            SearchError: If searching fails
        """
        pass


class EmbeddingProvider(ABC):
    """Interface for embedding providers.

    Embedding providers are responsible for generating embeddings
    for text.
    """

    @abstractmethod
    async def embed(self, text: str, **kwargs: Any) -> List[float]:
        """Generate an embedding for text.

        Args:
            text: The text to embed
            **kwargs: Additional arguments for embedding

        Returns:
            The embedding vector

        Raises:
            EmbeddingError: If embedding fails
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: The texts to embed
            **kwargs: Additional arguments for embedding

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding fails
        """
        pass


class RerankerProvider(ABC):
    """Interface for reranker providers.

    Reranker providers are responsible for reranking search results
    based on a query.
    """

    @abstractmethod
    async def rerank(
        self, query: str, documents: List[Document], **kwargs: Any
    ) -> List[ScoredChunk]:
        """Rerank documents based on a query.

        Args:
            query: The query to rerank for
            documents: The documents to rerank
            **kwargs: Additional arguments for reranking

        Returns:
            List of reranked documents with scores

        Raises:
            RerankError: If reranking fails
        """
        pass


class GenerationProvider(ABC):
    """Interface for generation providers.

    Generation providers are responsible for generating text
    based on a prompt.
    """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text.

        Args:
            prompt: The prompt to generate from
            **kwargs: Additional arguments for generation

        Returns:
            The generated text

        Raises:
            GenerationError: If generation fails
        """
        pass


# Pipeline interfaces
class PipelineStage(ABC):
    """Interface for pipeline stages.

    Pipeline stages are components in a processing pipeline
    that transform inputs into outputs.

    Note:
        This is a legacy interface. For new code, use
        `pepperpy.core.pipeline.base.PipelineStage` instead.

    Migration Guide:
        To migrate to the new framework:
        1. Import from pepperpy.core.pipeline.base instead:
            from pepperpy.core.pipeline.base import PipelineStage
        2. Create stages with proper type hints:
            class MyStage(PipelineStage[Input, Output]):
                async def process(self, data: Input, context: PipelineContext) -> Output:
                    ...

    Example:
        >>> from pepperpy.core.pipeline.base import PipelineStage, PipelineContext
        >>> from typing import List
        >>>
        >>> class TokenizerStage(PipelineStage[str, List[str]]):
        ...     def __init__(self):
        ...         super().__init__("tokenizer")
        ...
        ...     async def process(
        ...         self,
        ...         data: str,
        ...         context: PipelineContext,
        ...     ) -> List[str]:
        ...         return data.split()
    """

    @abstractmethod
    async def process(self, inputs: Any, **kwargs: Any) -> Any:
        """Process the stage inputs.

        Note:
            This is a legacy method. For new code, use the new framework's
            process method with proper type hints and context parameter.

        Args:
            inputs: The stage inputs
            **kwargs: Additional arguments for processing

        Returns:
            The stage outputs

        Raises:
            PipelineError: If processing fails
        """
        pass


class AbstractPipelineStage(Generic[Input, Output], ABC):
    """Generic interface for pipeline stages.

    This is a more strongly typed version of the PipelineStage interface.
    """

    @abstractmethod
    async def process(self, inputs: Input, **kwargs: Any) -> Output:
        """Process the stage inputs.

        Args:
            inputs: The stage inputs
            **kwargs: Additional arguments for processing

        Returns:
            The stage outputs

        Raises:
            PipelineError: If processing fails
        """
        pass
